"""RAG service: index a CurriculumPack and retrieve grounded, cited context.

Grounding unit today = a curriculum TOPIC (chapter title + topic title + its concept list).
That is the structured, copyright-safe substrate the constitution calls for (§38/§39) — full
textbook/question-paper ingestion is a later slice that reuses the same embed→index→retrieve
pipeline. Retrieval is always scoped to (school_id, pack_id); context carries citations so the
teacher/tutor can trace every grounded claim (§109.3).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import CurriculumChapter, CurriculumPack, CurriculumTopic
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.vectorstore import VectorPoint, collection_name, get_vector_store
from app.modules.ai.vectorstore.base import VectorStore

_NAMESPACE = "curriculum"


@dataclass
class RetrievedChunk:
    ref_id: str
    text: str
    score: float
    chapter: str | None
    topic: str | None
    pack_id: str


def _topic_text(chapter: CurriculumChapter, topic: CurriculumTopic) -> str:
    ch = f"{chapter.number + ' ' if chapter.number else ''}{chapter.title}".strip()
    concepts = topic.concepts or []
    concept_str = "; ".join(str(c) for c in concepts) if concepts else ""
    body = f"Chapter: {ch}\nTopic: {topic.title}"
    if concept_str:
        body += f"\nConcepts: {concept_str}"
    return body


class RagService:
    """Wires the shared EmbeddingService + VectorStore for curriculum grounding."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedder or EmbeddingService()
        self.store = store or get_vector_store()

    def _collection(self) -> str:
        return collection_name(_NAMESPACE, self.embedder.provider_name, self.embedder.dimensions())

    async def index_pack(self, pack: CurriculumPack) -> int:
        """Embed + index every topic of a pack. Idempotent per topic (stable point ids)."""
        chapters = list(
            (
                await self.db.execute(
                    select(CurriculumChapter)
                    .where(
                        CurriculumChapter.pack_id == pack.id,
                        CurriculumChapter.school_id == pack.school_id,
                    )
                    .order_by(CurriculumChapter.order_index)
                )
            ).scalars().all()
        )
        if not chapters:
            return 0
        chapter_by_id = {c.id: c for c in chapters}
        topics = list(
            (
                await self.db.execute(
                    select(CurriculumTopic)
                    .where(CurriculumTopic.chapter_id.in_(list(chapter_by_id)))
                    .order_by(CurriculumTopic.order_index)
                )
            ).scalars().all()
        )
        if not topics:
            return 0

        texts = [_topic_text(chapter_by_id[t.chapter_id], t) for t in topics]
        result = await self.embedder.embed(
            texts, feature="curriculum_ingest", school_id=str(pack.school_id)
        )

        points: list[VectorPoint] = []
        for topic, vector in zip(topics, result.vectors):
            chapter = chapter_by_id[topic.chapter_id]
            points.append(
                VectorPoint(
                    id=str(topic.id),
                    vector=vector,
                    payload={
                        "school_id": str(pack.school_id),
                        "pack_id": str(pack.id),
                        "class_id": str(pack.class_id),
                        "subject_id": str(pack.subject_id),
                        "chapter": chapter.title,
                        "topic": topic.title,
                        "text": _topic_text(chapter, topic),
                        "kind": "topic",
                    },
                )
            )

        collection = self._collection()
        await self.store.ensure_collection(collection, dimensions=result.dimensions)
        return await self.store.upsert(collection, points)

    async def retrieve(
        self,
        query: str,
        *,
        school_id: uuid.UUID | str,
        pack_id: uuid.UUID | str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Top-k topics for a query, hard-scoped to (school_id, pack_id)."""
        vector = await self.embedder.embed_one(
            query, feature="curriculum_retrieval", school_id=str(school_id)
        )
        matches = await self.store.search(
            self._collection(),
            vector,
            school_id=str(school_id),
            top_k=top_k,
            filters={"pack_id": str(pack_id)},
        )
        out: list[RetrievedChunk] = []
        for m in matches:
            p: dict[str, Any] = m.payload or {}
            out.append(
                RetrievedChunk(
                    ref_id=m.id,
                    text=p.get("text", ""),
                    score=m.score,
                    chapter=p.get("chapter"),
                    topic=p.get("topic"),
                    pack_id=p.get("pack_id", str(pack_id)),
                )
            )
        return out

    @staticmethod
    def build_context(chunks: list[RetrievedChunk]) -> str:
        """Assemble retrieved topics into a cited context block for prompt grounding.

        Each block is numbered and labelled with its source (chapter › topic) so the model can
        cite it and a human can trace it — ungrounded generation is not allowed (§109)."""
        if not chunks:
            return ""
        blocks = []
        for i, c in enumerate(chunks, start=1):
            source = " › ".join(x for x in (c.chapter, c.topic) if x) or "curriculum"
            blocks.append(f"[{i}] (source: {source})\n{c.text}")
        return "\n\n".join(blocks)
