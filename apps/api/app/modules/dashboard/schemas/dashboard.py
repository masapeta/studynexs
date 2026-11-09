"""Dashboard summary schemas — role-tailored home screen."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.dashboard.schemas.teacher_home import TeacherCommandCenterOut

SchoolAttendanceStatus = Literal["not_recorded", "in_progress", "attention_needed", "healthy"]


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


class MyClassOut(BaseModel):
    class_id: uuid.UUID
    class_label: str
    is_incharge: bool = False
    subjects: list[str] = Field(default_factory=list)


class InchargeClassSummaryOut(BaseModel):
    class_id: uuid.UUID
    class_label: str
    attendance_percent: float | None = None
    pending_qp_approvals: int = 0


class PrincipalInterventionEvidenceOut(BaseModel):
    label: str
    value: str
    href: str | None = None


class PrincipalInterventionOut(BaseModel):
    id: str
    severity: Literal["high", "medium"]
    issue: str
    why_it_matters: str
    affected_scope: str
    owner: str
    recommended_intervention: str
    status: str
    href: str
    evidence_chain_href: str
    evidence: list[PrincipalInterventionEvidenceOut] = Field(default_factory=list)


class DashboardSummaryOut(BaseModel):
    persona: Literal["admin", "operations", "class_incharge", "teacher"]
    subtitle: str
    teacher_home: TeacherCommandCenterOut | None = None
    # Admin-only school-wide stats
    total_students: int | None = None
    total_teachers: int | None = None
    total_classes: int | None = None
    pending_fees: float | None = None
    school_attendance_status: SchoolAttendanceStatus | None = None
    school_attendance_percent: float | None = None
    attendance_marked_today: int | None = None
    attendance_enrolled: int | None = None
    admissions_pipeline: int | None = None
    expenses_this_month: float | None = None
    class_performance: list[dict] = Field(default_factory=list)
    # Last 7 recorded school days of school-wide present %, oldest first (sparkline)
    attendance_trend: list[float] = Field(default_factory=list)
    pending_qp_approvals: int | None = None
    # Class incharge
    incharge_classes: list[InchargeClassSummaryOut] = Field(default_factory=list)
    # Subject teacher
    teaching_assignments: list[TeachingAssignmentOut] = Field(default_factory=list)
    my_draft_papers: int = 0
    # Principal / admin decision workspace
    principal_interventions: list[PrincipalInterventionOut] = Field(default_factory=list)
    # Staff home "My classes": exactly teaching ∪ incharge classes for scoped staff
    my_classes: list[MyClassOut] = Field(default_factory=list)
    # Operations
    upcoming_events: int | None = None
    # Shared
    quick_actions: list[QuickActionOut] = Field(default_factory=list)
    notices: list[NoticeBriefOut] = Field(default_factory=list)
