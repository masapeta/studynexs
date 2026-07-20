"""Lesson plan schemas."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class LessonSegmentOut(BaseModel):
    duration_min: int
    activity: str


class LessonPlanOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    chapter: str | None = None
    topic: str | None = None
    scheduled_for: date | None = None
    segments: list[LessonSegmentOut] = Field(default_factory=list)
    status: str
    notes: str | None = None
    pack_id: uuid.UUID | None = None
    pack_status: str | None = None
    pack_version: int | None = None
    grounded: bool = False
    grounding_sources: list[dict] | None = None
    ai_model: str | None = None
    grounded_at: date | None = None
    can_edit: bool = True
    can_approve: bool = False


class GenerateLessonPlanRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    topic: str | None = None
    chapter: str | None = None
    scheduled_for: date | None = None
    pack_id: uuid.UUID | None = None
    generation_mode: Literal["template", "copilot"] = "template"


class UpdateLessonPlanRequest(BaseModel):
    title: str | None = None
    chapter: str | None = None
    topic: str | None = None
    notes: str | None = None
    segments: list[LessonSegmentOut] | None = None
