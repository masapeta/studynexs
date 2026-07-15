"""Parent Copilot schemas — grounded parent briefings (Batch 27)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ParentFocusAreaOut(BaseModel):
    topic: str
    subject_name: str
    mastery_pct: float | None = None
    concept_slug: str | None = None


class ParentBriefingOut(BaseModel):
    student_id: uuid.UUID
    summary: str
    focus_areas: list[ParentFocusAreaOut] = Field(default_factory=list)
    home_tips: list[str] = Field(default_factory=list)
    encouragement: str = ""
    grounded: bool = False
    model: str | None = None


class ParentAskIn(BaseModel):
    question: str = Field(..., min_length=3, max_length=800)


class ParentAnswerOut(BaseModel):
    answer: str
    home_tips: list[str] = Field(default_factory=list)
    grounded: bool = False
    model: str | None = None
