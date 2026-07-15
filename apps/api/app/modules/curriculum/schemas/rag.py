"""RAG hybrid search response schemas (Batch 24)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RagSearchHitOut(BaseModel):
    ref_id: str
    text: str
    score: float
    chapter: str | None = None
    topic: str | None = None


class RagSearchOut(BaseModel):
    query: str
    pack_id: str
    hits: list[RagSearchHitOut] = Field(default_factory=list)
