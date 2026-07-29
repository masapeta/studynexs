"""Schemas for AI question-paper generation, review, and export."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models.examination import ExamType
from app.modules.ai.gateway.input_guard import (
    ALLOWED_DIFFICULTIES,
    sanitize_prompt_text,
    sanitize_topic_list,
)
from app.modules.ai.gateway.output_guard import sanitize_paper_sections
from app.modules.ai.question_paper_constraints import (
    QUESTION_OUTPUT_TOKEN_BUDGET,
    estimated_question_output_tokens,
)

QuestionType = Literal[
    "mcq",
    "fill_blank",
    "match",
    "true_false",
    "very_short",
    "short",
    "long",
    "very_long",
]
BloomLevel = Literal["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]


class SectionPlanIn(BaseModel):
    """Teacher-authored, exact section contract for Question Paper Studio generation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    type: QuestionType
    question_count: int = Field(ge=1, le=60)
    marks_per_question: Decimal = Field(gt=0, le=100, max_digits=5, decimal_places=2)
    instructions: str | None = Field(default=None, max_length=2000)

    @field_validator("title", mode="before")
    @classmethod
    def _sanitize_title(cls, value: object) -> str:
        return sanitize_prompt_text(str(value), max_length=200, field_name="section title")

    @field_validator("instructions", mode="before")
    @classmethod
    def _sanitize_instructions(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        return sanitize_prompt_text(
            str(value), max_length=2000, field_name="section instructions"
        )

    def as_service_plan(self) -> dict:
        return {
            "title": self.title,
            "type": self.type,
            "count": self.question_count,
            "marks_per_q": float(self.marks_per_question),
            "instructions": self.instructions or "",
        }


class BlueprintSlotIn(BaseModel):
    """One zero-based question coordinate with teacher-authoritative academic metadata."""

    model_config = ConfigDict(extra="forbid")

    section_index: int = Field(ge=0, le=23)
    question_index: int = Field(ge=0, le=59)
    chapter_id: uuid.UUID | None = None
    chapter: str = Field(min_length=1, max_length=200)
    bloom: BloomLevel

    @field_validator("chapter", mode="before")
    @classmethod
    def _sanitize_chapter(cls, value: object) -> str:
        return sanitize_prompt_text(
            str(value), max_length=200, field_name="blueprint chapter"
        )

    @field_validator("bloom", mode="before")
    @classmethod
    def _normalize_bloom(cls, value: object) -> str:
        normalized = str(value or "").strip().lower()
        aliases = {
            "remember": "Remember",
            "understand": "Understand",
            "apply": "Apply",
            "analyse": "Analyze",
            "analyze": "Analyze",
            "evaluate": "Evaluate",
            "create": "Create",
        }
        return aliases.get(normalized, str(value or "").strip())


class GenerateRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    exam_type: ExamType = ExamType.UNIT_TEST
    pack_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "APPROVED CurriculumPack to ground generation in. When set, every question is drawn "
            "from and cited to the pack's curriculum. New Studio requests require this unless "
            "the separately controlled manual-review exception is authorized."
        ),
    )
    topics: list[str] = Field(
        default_factory=list,
        description=(
            "Chapters/topics to focus on. With a pack_id these steer retrieval; without one "
            "they support legacy or explicitly authorized ungrounded draft generation."
        ),
        max_length=20,
    )
    total_marks: int = Field(default=80, ge=1, le=200)
    duration_minutes: int = Field(default=180, ge=15, le=360)
    difficulty: str = Field(default="balanced", description="easy | balanced | hard")
    title: str | None = Field(default=None, max_length=200)
    ungrounded_acknowledged: bool = Field(
        default=False,
        description=(
            "Authorized class authority acknowledgement for a Studio full-AI draft that is not "
            "grounded in an approved CurriculumPack. It never bypasses review or approval."
        ),
    )
    ungrounded_reason: str | None = Field(
        default=None,
        max_length=500,
        description="Required audit reason for the authorized ungrounded Studio exception.",
    )
    section_plan: list[SectionPlanIn] | None = Field(
        default=None,
        min_length=1,
        max_length=24,
        description=(
            "Optional exact teacher-authored section plan. Its effective marks must equal "
            "total_marks. When omitted, the legacy generated-paper blueprint remains unchanged."
        ),
    )
    blueprint_slots: list[BlueprintSlotIn] | None = Field(
        default=None,
        max_length=120,
        description=(
            "Optional complete zero-based map of every planned question to a chapter and "
            "Bloom level. Requires section_plan and must cover every coordinate exactly once."
        ),
    )

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

    @field_validator("ungrounded_reason", mode="before")
    @classmethod
    def _validate_ungrounded_reason(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(
            str(v), max_length=500, field_name="ungrounded reason", reject_injection=True
        )

    @field_validator("difficulty", mode="before")
    @classmethod
    def _validate_difficulty(cls, v: object) -> str:
        d = str(v or "balanced").strip().lower()
        if d not in ALLOWED_DIFFICULTIES:
            raise ValueError("difficulty must be easy, balanced, or hard")
        return d

    @model_validator(mode="after")
    def _validate_teacher_blueprint(self) -> GenerateRequest:
        if self.ungrounded_acknowledged and not self.ungrounded_reason:
            raise ValueError("ungrounded_reason is required with acknowledgement")
        if self.pack_id is not None and (
            self.ungrounded_acknowledged or self.ungrounded_reason is not None
        ):
            raise ValueError(
                "ungrounded acknowledgement and reason cannot accompany an approved pack"
            )
        if self.section_plan is None:
            if self.blueprint_slots:
                raise ValueError("blueprint_slots requires section_plan")
            return self

        titles = [section.title.casefold() for section in self.section_plan]
        if len(titles) != len(set(titles)):
            raise ValueError("section_plan titles must be unique")

        planned_question_count = sum(
            section.question_count for section in self.section_plan
        )
        if planned_question_count > 120:
            raise ValueError("section_plan may contain at most 120 questions")

        estimated_output = estimated_question_output_tokens(
            [(section.type, section.question_count) for section in self.section_plan]
        )
        if estimated_output > QUESTION_OUTPUT_TOKEN_BUDGET:
            raise ValueError(
                "section_plan is too large for one reliable generation; reduce the number "
                "of questions or split the paper into fewer long-answer sections"
            )

        planned_marks = sum(
            Decimal(section.question_count) * section.marks_per_question
            for section in self.section_plan
        )
        if planned_marks != Decimal(self.total_marks):
            raise ValueError(
                f"section_plan totals {planned_marks:g} marks; expected {self.total_marks}"
            )

        if self.blueprint_slots is None:
            return self

        expected = {
            (section_index, question_index)
            for section_index, section in enumerate(self.section_plan)
            for question_index in range(section.question_count)
        }
        actual = {
            (slot.section_index, slot.question_index) for slot in self.blueprint_slots
        }
        if len(actual) != len(self.blueprint_slots):
            raise ValueError("blueprint_slots contains duplicate question coordinates")
        if actual != expected:
            missing = len(expected - actual)
            unexpected = len(actual - expected)
            raise ValueError(
                "blueprint_slots must cover every planned question exactly once "
                f"(missing={missing}, unexpected={unexpected})"
            )
        return self


class BankSummaryOut(BaseModel):
    count: int
    class_id: uuid.UUID
    subject_id: uuid.UUID


class BankItemConceptOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    slug: str
    title: str
    order_index: int

    model_config = {"from_attributes": True}


class BankItemConceptsOut(BaseModel):
    item_id: uuid.UUID
    concepts: list[BankItemConceptOut] = Field(default_factory=list)


class QuestionOut(BaseModel):
    number: str                      # "1", "2(a)", etc.
    text: str
    marks: float
    type: str = "short"              # mcq | short | long | very_long | fill_blank
    options: list[str] | None = None  # for MCQ
    answer_key: str | None = None     # model answer / key (teacher-only)
    # Assessment-Intelligence metadata (present on curriculum-grounded papers).
    chapter: str | None = None        # teacher-selected blueprint chapter
    chapter_id: str | None = None     # stable CurriculumChapter reference when grounded
    bloom: str | None = None          # Bloom's level, e.g. "Understand", "Apply"
    difficulty: str | None = None     # easy | medium | hard
    learning_outcome: str | None = None
    concepts: list[str] | None = None
    citations: list[int] | None = None  # 1-based indices into paper.grounding_sources


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
    exam_type: ExamType = ExamType.UNIT_TEST
    total_marks: float
    duration_minutes: int | None = None
    general_instructions: str | None = None
    topics: list[str] | None = None
    difficulty_mix: dict | None = None
    sections: list[SectionOut] = Field(default_factory=list)
    status: str
    ai_model: str | None = None
    created_by: uuid.UUID | None = None
    # Curriculum grounding provenance (Assessment Intelligence).
    pack_id: uuid.UUID | None = None
    pack_status: str | None = None
    pack_version: int | None = None
    grounded: bool = False
    grounding_sources: list[dict] | None = None
    grounded_at: date | None = None
    ungrounded_reason: str | None = None
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
        return sanitize_prompt_text(
            str(v), max_length=200, field_name="title", reject_injection=True
        )

    @field_validator("general_instructions", mode="before")
    @classmethod
    def _sanitize_instructions(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(
            str(v), max_length=4000, field_name="general_instructions", reject_injection=True
        )

    @field_validator("sections", mode="before")
    @classmethod
    def _sanitize_sections(cls, v: object) -> list | None:
        if v is None:
            return None
        return sanitize_paper_sections(v)


class DuplicatePaperRequest(BaseModel):
    """Clone a paper into a fresh editable draft (zero LLM). Optionally re-target to another
    class; subject_id is required when class_id changes (subjects are class-scoped)."""
    title: str | None = None
    class_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None


class QuestionPaperFeedbackRequest(BaseModel):
    """Teacher quality signal for a generated paper; never changes the paper itself."""

    model_config = ConfigDict(extra="forbid")

    rating: Literal["up", "down"]
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("note", mode="before")
    @classmethod
    def _sanitize_note(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        return sanitize_prompt_text(
            str(value),
            max_length=2000,
            field_name="question paper feedback",
            reject_injection=False,
        )


class RejectPaperRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def _sanitize_reason(cls, v: object) -> str:
        cleaned = sanitize_prompt_text(str(v), max_length=500, field_name="reason")
        if not cleaned:
            raise ValueError("reason is required")
        return cleaned
