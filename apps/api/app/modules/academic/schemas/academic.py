"""Academic schemas — classes, subjects, enrollment, parent linking."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Class ────────────────────────────────────────────────────────────────────

class ClassOut(BaseModel):
    id: uuid.UUID
    grade: str
    section: str
    academic_year_id: uuid.UUID
    class_incharge_id: uuid.UUID | None = None
    class_incharge_name: str | None = None
    room_number: str | None = None
    created_at: datetime | None = None
    # Computed in list_classes; None means "no data yet" (vs a misleading 0/placeholder).
    student_count: int = 0
    attendance_pct: float | None = None
    avg_score: float | None = None
    model_config = ConfigDict(from_attributes=True)

class ClassCreate(BaseModel):
    grade: str = Field(..., examples=["Grade 5"])
    section: str = Field(..., examples=["A"])
    academic_year_id: uuid.UUID
    class_incharge_id: uuid.UUID | None = None
    room_number: str | None = None


class ClassRosterStudentOut(BaseModel):
    """Student row for class drill-down — includes term attendance %."""
    id: uuid.UUID
    admission_no: str
    roll_no: str | None = None
    student_name: str | None = None
    attendance_pct: float | None = None


# ── Subject ──────────────────────────────────────────────────────────────────

class SubjectOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str | None = None
    class_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class SubjectCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str | None = None
    class_id: uuid.UUID


# ── Student Enrollment ───────────────────────────────────────────────────────

class StudentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_no: str
    roll_no: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    student_name: str | None = None
    class_name: str | None = None
    parent_phone: str | None = None
    model_config = ConfigDict(from_attributes=True)

class StudentEnroll(BaseModel):
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_no: str = Field(..., max_length=50)
    roll_no: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None


# ── Parent Linking ───────────────────────────────────────────────────────────

class ParentLinkRequest(BaseModel):
    parent_user_id: uuid.UUID
    relationship: str = Field(..., examples=["father", "mother", "guardian"])
    is_primary: bool = False

class ParentLinkOut(BaseModel):
    student_id: uuid.UUID
    parent_id: uuid.UUID
    parent_name: str | None = None
    relationship: str | None = None
    is_primary: bool
    model_config = ConfigDict(from_attributes=True)


# ── Teacher Mapping ──────────────────────────────────────────────────────────

class TeacherMappingCreate(BaseModel):
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    class_id: uuid.UUID
    is_primary: bool = True

class TeacherMappingOut(BaseModel):
    id: uuid.UUID
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    class_id: uuid.UUID
    is_primary: bool
    model_config = ConfigDict(from_attributes=True)


# ── Student Lifecycle (DM-3b) ────────────────────────────────────────────────

class EnrollmentOut(BaseModel):
    """One student x academic-year membership record."""
    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    academic_year_id: uuid.UUID
    status: str
    roll_no: str | None = None
    enrolled_on: date | None = None
    ended_on: date | None = None
    class_name: str | None = None
    academic_year_label: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ClassChangeRequest(BaseModel):
    """
    Move a student to a different class within the SAME academic year —
    section rebalancing (8A -> 8B) or correcting a wrong admission class.

    Updates the current enrollment in place: one enrollment per student per
    year is preserved, and no historical attendance, marks, or receipts are
    touched.
    """
    class_id: uuid.UUID
    reason: str = Field(..., min_length=3, max_length=300)
    roll_no: str | None = Field(default=None, max_length=20)


class StudentExitRequest(BaseModel):
    """Transfer out / withdraw / mark alumni — closes the current enrollment."""
    reason: str = Field(..., min_length=3, max_length=300)
    effective_date: date | None = None


class StudentReadmitRequest(BaseModel):
    """Re-admit a previously exited student into a class for the current year."""
    class_id: uuid.UUID
    reason: str = Field(..., min_length=3, max_length=300)
    roll_no: str | None = Field(default=None, max_length=20)
    effective_date: date | None = None


class StudentLifecycleOut(BaseModel):
    """Result of a lifecycle transition."""
    student_id: uuid.UUID
    student_status: str
    class_id: uuid.UUID
    current_enrollment: EnrollmentOut | None = None
    fee_review_required: bool = False
    fee_review_note: str | None = None


# ── Bulk enrollment: promotion + section moves (DM-3c) ───────────────────────

PromotionOutcome = Literal["promoted", "detained", "graduated"]


class PromotionExclusion(BaseModel):
    """
    A student who does not follow the default "everyone moves up" rule.

    Detained students repeat the year, so they need an explicit
    ``target_class_id`` — the class they will repeat in. Graduating students
    take no target: they leave as alumni.
    """
    student_id: uuid.UUID
    outcome: PromotionOutcome
    target_class_id: uuid.UUID | None = None


class PromotionPreviewRequest(BaseModel):
    """Ask what a rollover would do, without doing it."""
    from_class_id: uuid.UUID
    to_class_id: uuid.UUID
    exclusions: list[PromotionExclusion] = Field(default_factory=list, max_length=500)


class PromotionCommitRequest(PromotionPreviewRequest):
    """Apply the rollover. Same inputs as the preview, plus a reason for the audit."""
    reason: str = Field(..., min_length=3, max_length=300)


class PromotionCandidateOut(BaseModel):
    """What will happen to one student — including why they were skipped."""
    student_id: uuid.UUID
    student_name: str | None = None
    admission_no: str | None = None
    roll_no: str | None = None
    outcome: str
    target_class_id: uuid.UUID | None = None
    target_class_label: str | None = None
    has_unsettled_dues: bool = False
    warnings: list[str] = Field(default_factory=list)


class PromotionPlanOut(BaseModel):
    """
    The rollover plan. ``commit`` returns the same shape as ``preview`` so an
    admin can compare what they approved with what actually happened.
    """
    from_class_id: uuid.UUID
    from_class_label: str
    from_year_label: str
    to_class_id: uuid.UUID
    to_class_label: str
    to_year_label: str
    candidates: list[PromotionCandidateOut] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
    # Present on commit only.
    enrollments_created: int | None = None
    enrollments_closed: int | None = None


class BulkClassChangeRequest(BaseModel):
    """
    Move students between sections of the same academic year.
    ``student_ids`` omitted means the whole class moves.
    """
    from_class_id: uuid.UUID
    to_class_id: uuid.UUID
    student_ids: list[uuid.UUID] | None = Field(default=None, max_length=500)
    reason: str = Field(..., min_length=3, max_length=300)


class BulkMovedStudentOut(BaseModel):
    student_id: uuid.UUID
    student_name: str | None = None
    fee_review_required: bool = False


class BulkSkippedStudentOut(BaseModel):
    student_id: uuid.UUID
    student_name: str | None = None
    reason: str


class BulkClassChangeOut(BaseModel):
    from_class_id: uuid.UUID
    from_class_label: str
    to_class_id: uuid.UUID
    to_class_label: str
    moved: list[BulkMovedStudentOut] = Field(default_factory=list)
    skipped: list[BulkSkippedStudentOut] = Field(default_factory=list)
    fee_review_required_count: int = 0
    fee_review_note: str | None = None
