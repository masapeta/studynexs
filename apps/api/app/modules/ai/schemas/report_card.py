"""Schemas for AI-assisted report cards (consolidation + remark)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    student_id: uuid.UUID
    title: str | None = None


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
    title: str | None = None
    ai_remark: str | None = None
