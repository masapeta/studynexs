"""Schemas for AI question-paper generation, review, and export."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    topics: list[str] = Field(default_factory=list, description="Chapters/topics to cover")
    total_marks: int = Field(default=80, ge=1, le=200)
    duration_minutes: int = Field(default=180, ge=15, le=360)
    difficulty: str = Field(default="balanced", description="easy | balanced | hard")
    title: str | None = None


class QuestionOut(BaseModel):
    number: str                      # "1", "2(a)", etc.
    text: str
    marks: float
    type: str = "short"              # mcq | short | long | very_long | fill_blank
    options: list[str] | None = None  # for MCQ
    answer_key: str | None = None     # model answer / key (teacher-only)


class SectionOut(BaseModel):
    title: str                        # "Section A"
    instructions: str | None = None
    questions: list[QuestionOut] = Field(default_factory=list)


class QuestionPaperOut(BaseModel):
    id: uuid.UUID
    title: str
    board: str
    grade: str
    subject_name: str
    total_marks: float
    duration_minutes: int | None = None
    general_instructions: str | None = None
    topics: list[str] | None = None
    difficulty_mix: dict | None = None
    sections: list[SectionOut] = Field(default_factory=list)
    status: str
    ai_model: str | None = None


class UpdatePaperRequest(BaseModel):
    """Teacher edits before approval — only the editable parts of the paper."""
    title: str | None = None
    general_instructions: str | None = None
    sections: list[SectionOut] | None = None


class DuplicatePaperRequest(BaseModel):
    """Clone a paper into a fresh editable draft (zero LLM). Optionally re-target to another
    class; subject_id is required when class_id changes (subjects are class-scoped)."""
    title: str | None = None
    class_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
