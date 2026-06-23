"""Examination schemas."""

import uuid
from datetime import date as date_type
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.examination import ExamType


class ExamCreate(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    exam_type: ExamType
    title: str = Field(..., max_length=200)
    total_marks: float
    exam_date: Optional[date_type] = None
    # Whole-exam chapter/topic tag (slip/unit tests map 1:1 to a chapter).
    topic: Optional[str] = Field(None, max_length=120)

class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    exam_type: ExamType
    title: str
    total_marks: float
    exam_date: Optional[date_type] = Field(None, validation_alias="date")
    topic: Optional[str] = None
    has_question_schema: bool = False
    source_paper_id: Optional[uuid.UUID] = None
    can_evaluate_sheets: bool = False

    @classmethod
    def from_exam(cls, exam) -> "ExamOut":
        out = cls.model_validate(exam)
        out.has_question_schema = bool(exam.question_schema)
        out.can_evaluate_sheets = bool(exam.source_paper_id and exam.question_schema)
        return out


class QuestionDef(BaseModel):
    no: str = Field(..., min_length=1, max_length=10)
    max_marks: float = Field(..., gt=0)
    topic: Optional[str] = Field(None, max_length=120)


class QuestionSchemaSet(BaseModel):
    # Either send questions directly, or set source_paper_id to copy no/max_marks
    # (and topic, when the paper has exactly one) from an approved AI question paper.
    questions: list[QuestionDef] = []
    source_paper_id: Optional[uuid.UUID] = None


class MarkEntry(BaseModel):
    student_id: uuid.UUID
    marks_obtained: float = 0
    # {qno: marks}; requires the exam to have a question_schema. When present,
    # marks_obtained is derived server-side as the sum (client value ignored).
    question_marks: dict[str, float] | None = None
    grade_letter: str | None = None
    remarks: str | None = None

class BulkMarkEntryRequest(BaseModel):
    exam_id: uuid.UUID
    entries: list[MarkEntry]

class ExamMarkOut(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    marks_obtained: float
    question_marks: dict[str, float] | None = None
    grade_letter: str | None = None
    remarks: str | None = None
    ai_feedback: str | None = None
    ai_graded: bool = False
    model_config = ConfigDict(from_attributes=True)
