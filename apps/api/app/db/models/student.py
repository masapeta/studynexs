"""Student & Parent models with multi-child linking."""
from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Relationship(str, enum.Enum):
    FATHER = "father"
    MOTHER = "mother"
    GUARDIAN = "guardian"


class StudentStatus(str, enum.Enum):
    """Lifecycle of a student within the school (DM-3)."""

    ACTIVE = "active"
    TRANSFERRED = "transferred"  # left for another school
    WITHDRAWN = "withdrawn"  # dropped out / removed
    ALUMNI = "alumni"  # completed final grade


class EnrollmentStatus(str, enum.Enum):
    """Outcome of one student × academic-year enrollment (DM-3)."""

    ACTIVE = "active"  # current enrollment
    PROMOTED = "promoted"  # moved up at year rollover
    DETAINED = "detained"  # repeating the grade
    TRANSFERRED = "transferred"  # left mid-year for another school
    WITHDRAWN = "withdrawn"  # dropped out mid-year
    COMPLETED = "completed"  # finished the school's final grade


class Student(BaseModel):
    __tablename__ = "students"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    admission_no: Mapped[str] = mapped_column(String(50), nullable=False)
    roll_no: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender))
    blood_group: Mapped[str | None] = mapped_column(String(5))
    admission_date: Mapped[date | None] = mapped_column(Date)
    apaar_number: Mapped[str | None] = mapped_column(String(30))  # APAAR/ABC ID
    # Lifecycle (DM-3). class_id above remains the denormalized "current class"
    # pointer; per-year history lives in enrollments.
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus), nullable=False, default=StudentStatus.ACTIVE,
        server_default=StudentStatus.ACTIVE.name,
    )

    # Relationships
    user = relationship("User", lazy="selectin")
    class_ = relationship("Class", lazy="selectin")
    parents = relationship("StudentParentMap", back_populates="student", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("school_id", "admission_no", name="uq_student_admission"),
        Index("ix_students_school_class", "school_id", "class_id"),
    )


class Enrollment(BaseModel):
    """
    One student × academic-year membership record (DM-3).

    students.class_id only knows the CURRENT class; year rollover would
    otherwise overwrite history. Promotion is additive: close this row
    (status promoted/detained/…, ended_on set) and insert the next year's
    row — the student's academic history is never destroyed.
    """

    __tablename__ = "enrollments"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.ACTIVE,
        server_default=EnrollmentStatus.ACTIVE.name,
    )
    roll_no: Mapped[str | None] = mapped_column(String(20))
    enrolled_on: Mapped[date | None] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)

    # Relationships
    student = relationship("Student", lazy="selectin")
    class_ = relationship("Class", lazy="selectin")
    academic_year = relationship("AcademicYear", lazy="selectin")

    __table_args__ = (
        # One enrollment per student per academic year.
        UniqueConstraint("student_id", "academic_year_id", name="uq_enrollment_student_year"),
        Index("ix_enrollments_school_class", "school_id", "class_id"),
        Index("ix_enrollments_student", "student_id"),
    )


class Parent(BaseModel):
    __tablename__ = "parents"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    relationship_type: Mapped[Relationship] = mapped_column(Enum(Relationship), nullable=False)

    # Relationships
    user = relationship("User", lazy="selectin")
    children = relationship("StudentParentMap", back_populates="parent", lazy="selectin")


class StudentParentMap(BaseModel):
    """
    Maps students to parents (many-to-many).
    One parent can have multiple children (siblings).
    One student can have multiple parents (father + mother).
    """
    __tablename__ = "student_parent_map"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parents.id"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    # Per-link relationship (expand-then-contract from Parent.relationship_type):
    # a user can be "father" to one student and "guardian" to another. Nullable
    # during migration; reads prefer this and fall back to Parent.relationship_type.
    relationship_type: Mapped[Relationship | None] = mapped_column(
        Enum(Relationship), nullable=True
    )

    # Relationships
    student = relationship("Student", back_populates="parents", lazy="selectin")
    parent = relationship("Parent", back_populates="children", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("student_id", "parent_id", name="uq_student_parent"),
    )
