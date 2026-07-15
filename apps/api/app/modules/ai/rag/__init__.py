"""Shared RAG platform — grounds academic AI in a school's approved CurriculumPack.

Indexes the pack's chapter→topic tree into the vector store (via the shared EmbeddingService),
and retrieves tenant- and pack-scoped context with source citations. All academic AI (QP
generation, tutor, evaluation) retrieves through this service rather than embedding free text.
"""

from app.modules.ai.rag.service import RagService, RetrievedChunk
from app.modules.ai.rag.hybrid import HybridRetrievalOptions, HybridRetrievalService

__all__ = ["RagService", "RetrievedChunk", "HybridRetrievalOptions", "HybridRetrievalService"]
