"""Academic schemas — classes, subjects, enrollment, parent linking."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Class ────────────────────────────────────────────────────────────────────

class ClassOut(BaseModel):
    id: uuid.UUID
    grade: str
    section: str
    academic_year_id: uuid.UUID
    class_incharge_id: uuid.UUID | None = None
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
