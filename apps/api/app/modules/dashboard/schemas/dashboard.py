"""Dashboard summary schemas — role-tailored home screen."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.dashboard.schemas.teacher_home import TeacherCommandCenterOut


class QuickActionOut(BaseModel):
    label: str
    href: str


class ClassAttendanceBarOut(BaseModel):
    label: str
    present: int
    strength: int
    percentage: float


class NoticeBriefOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    audience: str
    priority: str
    created_at: str | None = None


class TeachingAssignmentOut(BaseModel):
    class_id: uuid.UUID
    class_label: str
    subject_name: str


class InchargeClassSummaryOut(BaseModel):
    class_id: uuid.UUID
    class_label: str
    attendance_percent: float | None = None
    pending_qp_approvals: int = 0


class DashboardSummaryOut(BaseModel):
    persona: Literal["admin", "class_incharge", "teacher"]
    subtitle: str
    teacher_home: TeacherCommandCenterOut | None = None
    # Admin-only school-wide stats
    total_students: int | None = None
    total_teachers: int | None = None
    total_classes: int | None = None
    pending_fees: float | None = None
    school_attendance_percent: float | None = None
    admissions_pipeline: int | None = None
    expenses_this_month: float | None = None
    class_performance: list[dict] = Field(default_factory=list)
    pending_qp_approvals: int | None = None
    # Class incharge
    incharge_classes: list[InchargeClassSummaryOut] = Field(default_factory=list)
    # Subject teacher
    teaching_assignments: list[TeachingAssignmentOut] = Field(default_factory=list)
    my_draft_papers: int = 0
    # Shared
    quick_actions: list[QuickActionOut] = Field(default_factory=list)
    notices: list[NoticeBriefOut] = Field(default_factory=list)
