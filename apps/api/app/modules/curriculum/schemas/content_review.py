"""Content Review Queue schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models.content_review import (
    ContentReviewItemType,
    ContentReviewSource,
    ContentReviewStatus,
)


class ConceptCardDraftPayload(BaseModel):
    title: str = Field(..., max_length=200)
    explanation: str = Field(..., min_length=20, max_length=8000)
    examples: Optional[list[str]] = None
    hints: Optional[list[str]] = None
    visual_kind: str = Field(default="generic", max_length=50)


class EnqueueConceptGapRequest(BaseModel):
    """Teacher manually requests tutor content for a concept."""
    title: Optional[str] = Field(None, max_length=200)
    explanation: Optional[str] = Field(None, min_length=20, max_length=8000)
    examples: Optional[list[str]] = None
    hints: Optional[list[str]] = None


class ContentReviewUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    draft_payload: Optional[dict] = None


class RejectContentReviewRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)


class ContentReviewItemOut(BaseModel):
    id: uuid.UUID
    pack_id: uuid.UUID
    item_type: ContentReviewItemType
    status: ContentReviewStatus
    source: ContentReviewSource
    concept_id: Optional[uuid.UUID] = None
    source_ref_id: Optional[uuid.UUID] = None
    title: str
    draft_payload: dict
    result_card_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    concept_slug: Optional[str] = None
    concept_title: Optional[str] = None

    model_config = {"from_attributes": True}


class ContentReviewQueueOut(BaseModel):
    items: list[ContentReviewItemOut] = Field(default_factory=list)
    pending_count: int = 0
