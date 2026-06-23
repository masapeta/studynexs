"""Teacher command center — daily teaching workflow (not admin ERP)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class DashboardActionOut(BaseModel):
    label: str
    href: str
    variant: str = "primary"  # primary | outline | ghost


class TodayClassOut(BaseModel):
    slot_id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    class_label: str
    subject_name: str
    period_number: int
    start_time: str
    end_time: str
    room: str | None = None
    next_topic: str | None = None
    attendance_status: str  # done | pending | not_yours
    homework_pending: bool = False
    actions: list[DashboardActionOut] = Field(default_factory=list)


class LessonPlanSegmentOut(BaseModel):
    duration_min: int
    activity: str


class LessonPlanPreviewOut(BaseModel):
    id: uuid.UUID | None = None
    class_id: uuid.UUID
    subject_id: uuid.UUID
    class_label: str
    subject_name: str
    schedule_label: str
    chapter: str | None = None
    topic: str | None = None
    segments: list[LessonPlanSegmentOut] = Field(default_factory=list)
    status: str = "placeholder"
    actions: list[DashboardActionOut] = Field(default_factory=list)
    can_edit: bool = False
    can_approve: bool = False


class StudentAttentionOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    reason: str
    topic: str | None = None


class SubjectProgressOut(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    class_label: str
    subject_name: str
    average_mastery: float | None = None
    weak_concepts: list[str] = Field(default_factory=list)
    students_needing_attention: list[StudentAttentionOut] = Field(default_factory=list)


class TimetableSlotBriefOut(BaseModel):
    start_time: str
    class_label: str
    subject_name: str


class TimetableDayOut(BaseModel):
    day: str
    day_label: str
    slots: list[TimetableSlotBriefOut] = Field(default_factory=list)


class PendingWorkOut(BaseModel):
    kind: str
    label: str
    detail: str | None = None
    href: str
    count: int = 1


class TeacherNoticeOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    priority: str
    created_at: str | None = None
    acknowledged: bool = False
    can_acknowledge: bool = False


class TeacherCommandCenterOut(BaseModel):
    """Three zones: Now · Next · Watchlist — plus pending work and notices."""
    greeting: str
    tagline: str = "What do I need to teach, check, plan, and follow up today?"
    today_classes: list[TodayClassOut] = Field(default_factory=list)
    pending_work: list[PendingWorkOut] = Field(default_factory=list)
    lesson_plan: LessonPlanPreviewOut | None = None
    weekly_timetable: list[TimetableDayOut] = Field(default_factory=list)
    subject_progress: list[SubjectProgressOut] = Field(default_factory=list)
    staff_notices: list[TeacherNoticeOut] = Field(default_factory=list)
    school_notices: list[TeacherNoticeOut] = Field(default_factory=list)
