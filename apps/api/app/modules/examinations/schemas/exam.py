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

class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    exam_type: ExamType
    title: str
    total_marks: float
    exam_date: Optional[date_type] = Field(None, validation_alias="date")

class MarkEntry(BaseModel):
    student_id: uuid.UUID
    marks_obtained: float
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
    grade_letter: str | None = None
    remarks: str | None = None
    model_config = ConfigDict(from_attributes=True)
