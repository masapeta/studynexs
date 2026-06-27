"""Schemas for AI question-paper generation, review, and export."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator

from app.modules.ai.gateway.input_guard import ALLOWED_DIFFICULTIES, sanitize_prompt_text, sanitize_topic_list


class GenerateRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    topics: list[str] = Field(
        default_factory=list,
        description="Chapters/topics to cover (Phase 1 free-text; CurriculumPack grounding in Phase 1.5)",
        max_length=20,
    )
    total_marks: int = Field(default=80, ge=1, le=200)
    duration_minutes: int = Field(default=180, ge=15, le=360)
    difficulty: str = Field(default="balanced", description="easy | balanced | hard")
    title: str | None = Field(default=None, max_length=200)

    @field_validator("topics", mode="before")
    @classmethod
    def _validate_topics(cls, v: object) -> list[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("topics must be a list")
        return sanitize_topic_list([str(x) for x in v])

    @field_validator("title", mode="before")
    @classmethod
    def _validate_title(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(str(v), max_length=200, field_name="title")

    @field_validator("difficulty", mode="before")
    @classmethod
    def _validate_difficulty(cls, v: object) -> str:
        d = str(v or "balanced").strip().lower()
        if d not in ALLOWED_DIFFICULTIES:
            raise ValueError("difficulty must be easy, balanced, or hard")
        return d


class BankSummaryOut(BaseModel):
    count: int
    class_id: uuid.UUID
    subject_id: uuid.UUID


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
    created_by: uuid.UUID | None = None
    can_approve: bool = False
    can_edit: bool = False
    can_submit: bool = False
    can_reject: bool = False
    rejection_reason: str | None = None
    credits_used: int | None = None


class UpdatePaperRequest(BaseModel):
    """Teacher edits before approval — only the editable parts of the paper."""
    title: str | None = Field(default=None, max_length=200)
    general_instructions: str | None = Field(default=None, max_length=4000)
    sections: list[SectionOut] | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _sanitize_title(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(str(v), max_length=200, field_name="title", reject_injection=False)

    @field_validator("general_instructions", mode="before")
    @classmethod
    def _sanitize_instructions(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(
            str(v), max_length=4000, field_name="general_instructions", reject_injection=False
        )


class DuplicatePaperRequest(BaseModel):
    """Clone a paper into a fresh editable draft (zero LLM). Optionally re-target to another
    class; subject_id is required when class_id changes (subjects are class-scoped)."""
    title: str | None = None
    class_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None


class RejectPaperRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
