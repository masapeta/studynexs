"""Tutor lesson schemas — teacher-style explain + visualize + practice."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class TutorStepOut(BaseModel):
    id: str
    title: str
    narration: str
    visual_kind: str  # fraction_bars | number_line | photosynthesis | triangle | equation | generic
    caption: Optional[str] = None


class TutorLessonOut(BaseModel):
    lesson_key: str
    topic: str
    subject_name: str
    mastery_pct: Optional[float] = None
    trigger: str  # exam_mistake | weak_topic | demo
    mistake_summary: Optional[str] = None
    pack_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    concept_slug: Optional[str] = None
    steps: list[TutorStepOut] = Field(default_factory=list)


class TutorRecommendationOut(BaseModel):
    lesson_key: str
    topic: str
    subject_name: str
    mastery_pct: Optional[float] = None
    reason: str
    pack_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    concept_slug: Optional[str] = None
    source: str = "template"
