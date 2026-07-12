"""ConceptCard API schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models.concept_card import ConceptCardStatus


class ConceptCardCreate(BaseModel):
    title: str = Field(..., max_length=200)
    explanation: str = Field(..., min_length=20, max_length=8000)
    examples: Optional[list[str]] = None
    hints: Optional[list[str]] = None
    visual_kind: str = Field(default="generic", max_length=50)


class ConceptCardUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    explanation: Optional[str] = Field(None, min_length=20, max_length=8000)
    examples: Optional[list[str]] = None
    hints: Optional[list[str]] = None
    visual_kind: Optional[str] = Field(None, max_length=50)


class ConceptCardOut(BaseModel):
    id: uuid.UUID
    pack_id: uuid.UUID
    concept_id: uuid.UUID
    title: str
    explanation: str
    examples: Optional[list[str]] = None
    hints: Optional[list[str]] = None
    visual_kind: str
    status: ConceptCardStatus
    created_by: uuid.UUID
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    concept_slug: Optional[str] = None
    concept_title: Optional[str] = None

    model_config = {"from_attributes": True}
