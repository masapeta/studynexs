"""Assessment Intelligence grounding — the seam between generation/evaluation and the RAG platform.

Flow: Teacher → Assessment Intelligence → RAG → Embedding → Vector store → provider.
This module is the "→ RAG" hop: it turns a school's APPROVED CurriculumPack into a cited context
block for grounded question-paper generation **and** (best-effort) answer-sheet marking. It talks
ONLY to the shared ``RagService`` (never a provider SDK, embedder, or vector store directly), so the
provider-agnostic contract and the tenant + pack isolation guarantees of the platform hold
automatically (CLAUDE.md §4.1, §32, §39).

Retrieval is chapter/topic-aware:
- when topics are named, each topic is retrieved on its own (precise, per-topic grounding);
- otherwise a single broad retrieval with a high ``top_k`` returns the whole pack's topic set.
Either way the result is deduplicated, capped, and numbered so per-question ``citations`` line up
with the numbered sources in ``context_text``.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import CurriculumPack, PackStatus
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.rag import RagService, RetrievedChunk
from app.modules.ai.vectorstore.base import VectorStore

logger = structlog.get_logger()

# A paper grounds on many topics; keep the context bounded so the prompt stays within budget.
_MAX_GROUNDING_CHUNKS = 24
_MAX_EVAL_GROUNDING_CHUNKS = 12
_PER_TOPIC_TOP_K = 4


@dataclass
class GroundingContext:
    """Cited curriculum context for a grounded generation call.

    ``context_text`` is the numbered, source-labelled block injected into the prompt.
    ``sources`` is the parallel machine-readable trace stored on the paper — index N in
    ``sources`` is the block ``[N]`` in ``context_text`` and the target of a question's
    ``citations: [N]``.
    """

    context_text: str
    sources: list[dict] = field(default_factory=list)

    @property
    def chunk_count(self) -> int:
        return len(self.sources)

    @property
    def is_empty(self) -> bool:
        return not self.sources


def _dedupe_ranked(chunk_lists: list[list[RetrievedChunk]]) -> list[RetrievedChunk]:
    """Merge per-topic retrievals: best score per topic (ref_id), highest score first."""
    best: dict[str, RetrievedChunk] = {}
    for chunks in chunk_lists:
        for c in chunks:
            existing = best.get(c.ref_id)
            if existing is None or c.score > existing.score:
                best[c.ref_id] = c
    return sorted(best.values(), key=lambda c: c.score, reverse=True)


async def ground_for_pack(
    db: AsyncSession,
    *,
    pack: CurriculumPack,
    topics: list[str] | None,
    embedder: EmbeddingService | None = None,
    store: VectorStore | None = None,
    max_chunks: int = _MAX_GROUNDING_CHUNKS,
) -> GroundingContext:
    """Retrieve pack-scoped curriculum context for grounding a question paper.

    Self-heals: if the pack has never been indexed, it is indexed on first use (idempotent).
    Returns an empty context (``is_empty``) when the pack has no chapters/topics — the caller
    must refuse to generate rather than fall back to ungrounded output (CLAUDE.md §109).
    """
    rag = RagService(db, embedder=embedder, store=store)
    school_id = pack.school_id

    # Ensure the pack is indexed. A cheap probe avoids re-embedding an already-indexed pack;
    # index_pack is idempotent (stable per-topic point ids) so a redundant call is harmless.
    probe = await rag.retrieve(
        pack.book_title or "syllabus", school_id=school_id, pack_id=pack.id, top_k=1
    )
    if not probe:
        indexed = await rag.index_pack(pack)
        if indexed == 0:
            return GroundingContext(context_text="", sources=[])

    clean_topics = [t.strip() for t in (topics or []) if t and t.strip()]
    if clean_topics:
        # Chapter/topic-aware: retrieve each named topic on its own, then merge.
        chunk_lists = [
            await rag.retrieve(
                topic, school_id=school_id, pack_id=pack.id, top_k=_PER_TOPIC_TOP_K
            )
            for topic in clean_topics
        ]
        chunks = _dedupe_ranked(chunk_lists)
    else:
        # No topics named → ground on the whole pack (broad retrieval, high top_k).
        chunks = await rag.retrieve(
            pack.book_title or "full prescribed syllabus for this subject",
            school_id=school_id,
            pack_id=pack.id,
            top_k=max_chunks,
        )

    chunks = chunks[:max_chunks]
    if not chunks:
        return GroundingContext(context_text="", sources=[])

    context_text = RagService.build_context(chunks)
    sources = [
        {
            "index": i,
            "chapter": c.chapter,
            "topic": c.topic,
            "ref_id": c.ref_id,
        }
        for i, c in enumerate(chunks, start=1)
    ]
    return GroundingContext(context_text=context_text, sources=sources)


async def ground_for_evaluation(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID | None,
    topics: list[str] | None = None,
    embedder: EmbeddingService | None = None,
    store: VectorStore | None = None,
) -> GroundingContext:
    """Best-effort curriculum grounding for answer-sheet marking.

    Unlike ``ground_for_pack`` at generation time, this **never raises** and never blocks marking.
    When the source paper has no pack, the pack is unapproved, or retrieval fails, an empty context
    is returned and the engine marks from the answer key alone. Grounding only improves suggestions.
    """
    empty = GroundingContext(context_text="", sources=[])
    if not pack_id:
        return empty
    try:
        pack = (
            await db.execute(
                select(CurriculumPack).where(
                    CurriculumPack.id == pack_id,
                    CurriculumPack.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if pack is None or pack.status != PackStatus.APPROVED:
            return empty
        return await ground_for_pack(
            db,
            pack=pack,
            topics=topics,
            embedder=embedder,
            store=store,
            max_chunks=_MAX_EVAL_GROUNDING_CHUNKS,
        )
    except Exception:
        logger.warning(
            "ground_for_evaluation_failed",
            school_id=str(school_id),
            pack_id=str(pack_id),
            exc_info=True,
        )
        return empty


def resolve_citations(sources: list[dict], indices: list[int]) -> list[dict]:
    """Map a question's citation indices back to their source rows (for display/verification)."""
    by_index = {int(s["index"]): s for s in sources if "index" in s}
    out: list[dict] = []
    for n in indices:
        src = by_index.get(int(n))
        if src is not None:
            out.append(src)
    return out


def as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
