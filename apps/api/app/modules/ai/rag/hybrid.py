"""Hybrid RAG retrieval — vector search + graph signals + re-ranking (Batch 24).

Combines dense vector retrieval with knowledge-graph concept/topic expansion and a lightweight
re-ranker so copilot grounding prefers syllabus-aligned, concept-rich topics.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import CurriculumChapter, CurriculumTopic
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge, KgEdgeType, KgNodeType
from app.modules.ai.rag.service import RagService, RetrievedChunk, _topic_text

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 2}


@dataclass
class HybridRetrievalOptions:
    """Optional graph-aware retrieval hints."""

    concept_ids: list[uuid.UUID] | None = None
    student_id: uuid.UUID | None = None
    rerank: bool = True
    candidate_multiplier: int = 3


@dataclass
class _TopicGraphSignals:
    concept_labels: set[str] = field(default_factory=set)
    has_approved_card: bool = False
    weak_student_hits: int = 0
    concept_id_hits: int = 0


@dataclass
class HybridRetrievalService:
    """Graph-augmented retrieval layered on ``RagService``."""

    db: AsyncSession
    rag: RagService

    async def retrieve_hybrid(
        self,
        query: str,
        *,
        school_id: uuid.UUID | str,
        pack_id: uuid.UUID | str,
        top_k: int = 5,
        options: HybridRetrievalOptions | None = None,
    ) -> list[RetrievedChunk]:
        opts = options or HybridRetrievalOptions()
        sid = uuid.UUID(str(school_id))
        pid = uuid.UUID(str(pack_id))
        candidate_k = max(top_k, top_k * opts.candidate_multiplier)

        vector_hits = await self.rag.retrieve(
            query, school_id=sid, pack_id=pid, top_k=candidate_k
        )
        expanded = await self._expand_via_concepts(
            query, school_id=sid, pack_id=pid, existing=vector_hits
        )
        merged = self._merge_by_ref(vector_hits + expanded)
        if not merged:
            return []

        topic_ids = [uuid.UUID(c.ref_id) for c in merged if c.ref_id]
        signals = await self._load_topic_signals(
            school_id=sid,
            pack_id=pid,
            topic_ids=topic_ids,
            concept_ids=opts.concept_ids,
            student_id=opts.student_id,
        )
        query_tokens = _tokens(query)

        if opts.rerank:
            reranked = [
                self._rerank_chunk(c, query_tokens=query_tokens, signals=signals.get(c.ref_id))
                for c in merged
            ]
            reranked.sort(key=lambda c: c.score, reverse=True)
            return reranked[:top_k]

        return merged[:top_k]

    async def _expand_via_concepts(
        self,
        query: str,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        existing: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Inject topics whose concepts lexically match the query (graph expansion)."""
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        concepts = list(
            (
                await self.db.execute(
                    select(CurriculumConcept).where(
                        CurriculumConcept.school_id == school_id,
                        CurriculumConcept.pack_id == pack_id,
                    )
                )
            ).scalars().all()
        )
        if not concepts:
            return []

        seen_refs = {c.ref_id for c in existing}
        matched_topic_ids: set[uuid.UUID] = set()
        for concept in concepts:
            labels = _tokens(concept.slug) | _tokens(concept.title)
            if labels & query_tokens:
                matched_topic_ids.add(concept.topic_id)

        if not matched_topic_ids:
            return []

        topics = list(
            (
                await self.db.execute(
                    select(CurriculumTopic).where(
                        CurriculumTopic.id.in_(matched_topic_ids),
                        CurriculumTopic.school_id == school_id,
                    )
                )
            ).scalars().all()
        )
        if not topics:
            return []

        chapter_ids = {t.chapter_id for t in topics}
        chapters = {
            c.id: c
            for c in (
                await self.db.execute(
                    select(CurriculumChapter).where(CurriculumChapter.id.in_(chapter_ids))
                )
            ).scalars().all()
        }

        out: list[RetrievedChunk] = []
        for topic in topics:
            ref = str(topic.id)
            if ref in seen_refs:
                continue
            chapter = chapters.get(topic.chapter_id)
            if chapter is None:
                continue
            out.append(
                RetrievedChunk(
                    ref_id=ref,
                    text=_topic_text(chapter, topic),
                    score=0.45,
                    chapter=chapter.title,
                    topic=topic.title,
                    pack_id=str(pack_id),
                )
            )
        return out

    async def _load_topic_signals(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        topic_ids: list[uuid.UUID],
        concept_ids: list[uuid.UUID] | None,
        student_id: uuid.UUID | None,
    ) -> dict[str, _TopicGraphSignals]:
        if not topic_ids:
            return {}

        concepts = list(
            (
                await self.db.execute(
                    select(CurriculumConcept).where(
                        CurriculumConcept.school_id == school_id,
                        CurriculumConcept.pack_id == pack_id,
                        CurriculumConcept.topic_id.in_(topic_ids),
                    )
                )
            ).scalars().all()
        )
        by_topic: dict[uuid.UUID, list[CurriculumConcept]] = {}
        concept_id_set = set(concept_ids or [])
        for c in concepts:
            by_topic.setdefault(c.topic_id, []).append(c)

        approved_concept_ids: set[uuid.UUID] = set()
        if concepts:
            approved_concept_ids = set(
                (
                    await self.db.execute(
                        select(ConceptCard.concept_id).where(
                            ConceptCard.school_id == school_id,
                            ConceptCard.concept_id.in_([c.id for c in concepts]),
                            ConceptCard.status == ConceptCardStatus.APPROVED,
                        )
                    )
                ).scalars().all()
            )

        weak_topic_ids: set[uuid.UUID] = set()
        if student_id and concepts:
            weak_concept_ids = set(
                (
                    await self.db.execute(
                        select(KgEdge.to_id).where(
                            KgEdge.school_id == school_id,
                            KgEdge.pack_id == pack_id,
                            KgEdge.edge_type == KgEdgeType.STRUGGLES_WITH,
                            KgEdge.from_node_type == KgNodeType.STUDENT,
                            KgEdge.from_id == student_id,
                            KgEdge.to_node_type == KgNodeType.CONCEPT,
                            KgEdge.to_id.in_([c.id for c in concepts]),
                        )
                    )
                ).scalars().all()
            )
            for concept in concepts:
                if concept.id in weak_concept_ids:
                    weak_topic_ids.add(concept.topic_id)

        signals: dict[str, _TopicGraphSignals] = {}
        for topic_id in topic_ids:
            topic_concepts = by_topic.get(topic_id, [])
            labels: set[str] = set()
            has_card = False
            concept_hits = 0
            for concept in topic_concepts:
                labels |= _tokens(concept.slug)
                labels |= _tokens(concept.title)
                if concept.id in approved_concept_ids:
                    has_card = True
                if concept.id in concept_id_set:
                    concept_hits += 1
            signals[str(topic_id)] = _TopicGraphSignals(
                concept_labels=labels,
                has_approved_card=has_card,
                weak_student_hits=1 if topic_id in weak_topic_ids else 0,
                concept_id_hits=concept_hits,
            )
        return signals

    @staticmethod
    def _merge_by_ref(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        best: dict[str, RetrievedChunk] = {}
        for chunk in chunks:
            existing = best.get(chunk.ref_id)
            if existing is None or chunk.score > existing.score:
                best[chunk.ref_id] = chunk
        return list(best.values())

    @staticmethod
    def _rerank_chunk(
        chunk: RetrievedChunk,
        *,
        query_tokens: set[str],
        signals: _TopicGraphSignals | None,
    ) -> RetrievedChunk:
        base = float(chunk.score)
        boost = 0.0
        chunk_tokens = _tokens(chunk.text) | _tokens(chunk.topic or "")

        overlap = len(query_tokens & chunk_tokens)
        if overlap:
            boost += min(0.12, 0.04 * overlap)

        if signals:
            concept_overlap = len(query_tokens & signals.concept_labels)
            if concept_overlap:
                boost += min(0.18, 0.06 * concept_overlap)
            if signals.has_approved_card:
                boost += 0.05
            if signals.weak_student_hits:
                boost += 0.08
            boost += min(0.15, 0.05 * signals.concept_id_hits)

        return RetrievedChunk(
            ref_id=chunk.ref_id,
            text=chunk.text,
            score=base + boost,
            chapter=chunk.chapter,
            topic=chunk.topic,
            pack_id=chunk.pack_id,
        )
