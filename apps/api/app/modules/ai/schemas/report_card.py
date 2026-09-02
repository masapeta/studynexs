"""Schemas for AI-assisted report cards (consolidation + remark)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator

from app.db.models.examination import ExamType
from app.modules.ai.gateway.input_guard import sanitize_prompt_text


class GenerateReportRequest(BaseModel):
    student_id: uuid.UUID
    title: str | None = Field(default=None, max_length=200)
    academic_year_id: uuid.UUID | None = None
    exam_type: ExamType | None = None

    @field_validator("title", mode="before")
    @classmethod
    def _validate_title(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(str(v), max_length=200, field_name="title")


class SubjectRow(BaseModel):
    subject: str
    marks_obtained: float
    total_marks: float


class ReportCardOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    title: str
    student_name: str
    class_name: str
    subjects: list[SubjectRow]
    not_assessed: list[str] = []
    total_obtained: float
    total_max: float
    percentage: float
    overall_grade: str | None = None
    attendance_percentage: float | None = None
    ai_remark: str | None = None
    status: str
    ai_model: str | None = None


class UpdateReportRequest(BaseModel):
    """Teacher edits before approval — primarily the remark."""
    title: str | None = Field(default=None, max_length=200)
    ai_remark: str | None = Field(default=None, max_length=4000)

    @field_validator("title", mode="before")
    @classmethod
    def _sanitize_title(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(str(v), max_length=200, field_name="title", reject_injection=True)

    @field_validator("ai_remark", mode="before")
    @classmethod
    def _sanitize_remark(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_prompt_text(
            str(v), max_length=4000, field_name="ai_remark", reject_injection=True
        )
