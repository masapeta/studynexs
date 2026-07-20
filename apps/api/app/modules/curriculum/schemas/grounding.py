"""Curriculum grounding API schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CurriculumGroundingOut(BaseModel):
    pack_id: uuid.UUID
    pack_status: str
    pack_version: int
    source_count: int
    sources: list[dict] = Field(default_factory=list)
    context_preview: str = Field(
        description="First ~500 chars of grounded context for verification."
    )
