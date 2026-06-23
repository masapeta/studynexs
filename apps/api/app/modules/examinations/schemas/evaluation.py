"""Answer sheet evaluation schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCreate(BaseModel):
    student_id: uuid.UUID
    file_id: Optional[uuid.UUID] = None
    # Transcribed answers keyed by question number — used when OCR/vision is unavailable.
    student_answers: dict[str, str] = Field(default_factory=dict)


class QuestionSuggestion(BaseModel):
    marks_suggested: float
    max_marks: float
    feedback: str
    confidence: float = Field(ge=0, le=1)
    student_answer: str = ""


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


class MisconceptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    question_no: Optional[str] = None
    common_mistake: str
    remedial_activity: Optional[str] = None
    occurrence_count: int
    created_at: Optional[datetime] = None


class EvaluationApprove(BaseModel):
    teacher_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)
    correction_summary: Optional[str] = None


class CorrectionHistoryItem(BaseModel):
    evaluation_id: uuid.UUID
    exam_id: uuid.UUID
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
