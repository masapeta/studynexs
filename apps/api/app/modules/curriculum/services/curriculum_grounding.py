"""Curriculum Intelligence — shared grounding facade for all AI capabilities.

Every feature that needs approved curriculum context (question papers, lesson plans, …)
retrieves through this module. Capabilities must not call RagService or HybridRetrieval
directly for pack grounding — they use ``ground_approved_pack`` so pack validation,
Hybrid RAG retrieval, and provenance metadata stay consistent and tenant-scoped.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import PackStatus
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.services.assessment_grounding import ground_for_pack
from app.modules.ai.vectorstore.base import VectorStore
from app.modules.curriculum.services.pack_service import PackError, PackService


@dataclass
class CurriculumGrounding:
    """Approved-pack curriculum context with provenance for AI grounding."""

    pack_id: uuid.UUID
    pack_status: str
    pack_version: int
    context_text: str
    board: str | None = None
    sources: list[dict] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.sources

    @property
    def chunk_count(self) -> int:
        return len(self.sources)

    def as_metadata(self) -> dict:
        return {
            "pack_id": str(self.pack_id),
            "pack_status": self.pack_status,
            "pack_version": self.pack_version,
            "source_count": self.chunk_count,
            "sources": self.sources,
        }


async def ground_approved_pack(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
    class_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    topics: list[str] | None = None,
    embedder: EmbeddingService | None = None,
    store: VectorStore | None = None,
) -> CurriculumGrounding:
    """Retrieve curriculum from an APPROVED pack via the Hybrid RAG pipeline."""
    try:
        pack = await PackService(db).get_pack(school_id, pack_id)
    except PackError as exc:
        raise ValueError(str(exc)) from exc

    if class_id is not None and pack.class_id != class_id:
        raise ValueError("Curriculum pack does not match this class.")
    if subject_id is not None and pack.subject_id != subject_id:
        raise ValueError("Curriculum pack does not match this subject.")
    if pack.status != PackStatus.APPROVED:
        raise ValueError(
            "Approve the curriculum pack before using it for AI grounding."
        )

    ctx = await ground_for_pack(
        db, pack=pack, topics=topics, embedder=embedder, store=store
    )
    sources = [
        {
            **src,
            "pack_id": str(pack.id),
            "pack_status": pack.status.value,
            "pack_version": pack.version,
        }
        for src in ctx.sources
    ]
    return CurriculumGrounding(
        pack_id=pack.id,
        pack_status=pack.status.value,
        pack_version=pack.version,
        board=pack.board,
        context_text=ctx.context_text,
        sources=sources,
    )
