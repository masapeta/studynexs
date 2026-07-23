"""Answer sheet evaluation schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.ai.gateway.input_guard import sanitize_answer_map, sanitize_prompt_text


class EvaluationCreate(BaseModel):
    student_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    # Transcribed answers keyed by question number — used when OCR/vision is unavailable.
    student_answers: dict[str, str] = Field(default_factory=dict)

    @field_validator("student_answers", mode="before")
    @classmethod
    def _validate_answers(cls, v: object) -> dict[str, str]:
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("student_answers must be an object")
        return sanitize_answer_map({str(k): str(val) for k, val in v.items()})

    @model_validator(mode="after")
    def _require_input(self) -> "EvaluationCreate":
        if not self.file_id and not self.student_answers:
            raise ValueError("Provide an answer sheet image or transcribed answers")
        return self


class QuestionSuggestion(BaseModel):
    marks_suggested: float
    max_marks: float
    feedback: str
    confidence: float = Field(ge=0, le=1)
    student_answer: str = ""
    method: Optional[str] = None
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    status: str
    ai_suggestions: dict[str, Any] | None = None
    correction_summary: Optional[str] = None
    teacher_overrides: dict[str, Any] | None = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    error_message: Optional[str] = None
    job_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    question_paper_id: Optional[uuid.UUID] = None
    curriculum_pack_id: Optional[uuid.UUID] = None
    question_paper_grounded: bool = False
    evaluation_grounded: bool = False
    citation_ids: list[str] = Field(default_factory=list)
    evidence_ledger: dict[str, Any] | None = None


class MisconceptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    student_id: uuid.UUID | None = None
    source_evaluation_id: uuid.UUID | None = None
    topic: str
    question_no: Optional[str] = None
    common_mistake: str
    remedial_activity: Optional[str] = None
    occurrence_count: int
    created_at: Optional[datetime] = None


class EvaluationApprove(BaseModel):
    teacher_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)
    correction_summary: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("teacher_overrides", mode="before")
    @classmethod
    def _limit_overrides(cls, v: object) -> dict[str, dict[str, Any]]:
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("teacher_overrides must be an object")
        if len(v) > 100:
            raise ValueError("At most 100 question overrides allowed")
        return v

    @field_validator("correction_summary", mode="before")
    @classmethod
    def _sanitize_summary(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(
            str(v), max_length=2000, field_name="correction_summary", reject_injection=True
        )


class CorrectionHistoryItem(BaseModel):
    evaluation_id: uuid.UUID
    exam_id: uuid.UUID
    question_paper_id: Optional[uuid.UUID] = None
    curriculum_pack_id: Optional[uuid.UUID] = None
    question_paper_grounded: bool = False
    evaluation_grounded: bool = False
    exam_title: str
    student_id: uuid.UUID
    question_no: str
    ai_marks: float
    teacher_marks: float
    max_marks: float
    ai_feedback: str
    override_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    topic: Optional[str] = None
    method: Optional[str] = None
    citation_ids: list[str] = Field(default_factory=list)
