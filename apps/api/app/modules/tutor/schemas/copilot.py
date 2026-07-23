"""Student Copilot schemas — grounded study assistance (Batch 25)."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class WeakConceptStudyOut(BaseModel):
    concept_id: uuid.UUID
    slug: str
    title: str
    pack_id: uuid.UUID
    mastery_topic: Optional[str] = None
    mastery_pct: Optional[float] = None
    has_approved_card: bool = False


class StudyContextOut(BaseModel):
    student_id: uuid.UUID
    weak_concepts: list[WeakConceptStudyOut] = Field(default_factory=list)
    primary_concept_slug: Optional[str] = None
    curriculum_context: str = ""
    source_count: int = 0
    grounded: bool = False


class DailyLearningPlanOut(BaseModel):
    student_id: uuid.UUID
    status: str  # ready | empty
    title: str
    reason: str
    recommended_action: str
    topic: Optional[str] = None
    mastery_topic: Optional[str] = None
    mastery_pct: Optional[float] = None
    lesson_key: Optional[str] = None
    pack_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    concept_slug: Optional[str] = None
    source_count: int = 0
    grounded: bool = False
    fallback: bool = False
    evidence_summary: str = ""
    next_steps: list[str] = Field(default_factory=list)


class CopilotAskIn(BaseModel):
    question: str = Field(..., min_length=3, max_length=800)
    concept_slug: Optional[str] = Field(None, max_length=120)


class CopilotAnswerOut(BaseModel):
    answer: str
    concept_slug: Optional[str] = None
    concept_title: Optional[str] = None
    pack_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    source_count: int = 0
    citations: list[int] = Field(default_factory=list)
    follow_up_hints: list[str] = Field(default_factory=list)
    grounded: bool = False
    model: Optional[str] = None
