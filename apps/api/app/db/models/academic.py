"""Academic models — AcademicYear, Class, Subject, TeacherSubjectMapping."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class AcademicYear(BaseModel):
    __tablename__ = "academic_years"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    year_label: Mapped[str] = mapped_column(String(20), nullable=False)  # "2026-2027"
    start_date: Mapped[str] = mapped_column(Date, nullable=False)
    end_date: Mapped[str] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("school_id", "year_label", name="uq_school_academic_year"),
    )


class Class(BaseModel):
    __tablename__ = "classes"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    grade: Mapped[str] = mapped_column(String(20), nullable=False)  # "Grade 1", "Grade 8"
    section: Mapped[str] = mapped_column(String(5), nullable=False)  # "A", "B", "C", "D"
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    class_incharge_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    room_number: Mapped[str | None] = mapped_column(String(20))

    # Relationships
    academic_year = relationship("AcademicYear", lazy="selectin")
    class_incharge = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("school_id", "grade", "section", "academic_year_id", name="uq_class"),
        Index("ix_classes_school", "school_id"),
    )


class Subject(BaseModel):
    __tablename__ = "subjects"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20))
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )

    # Relationships
    class_ = relationship("Class", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("school_id", "name", "class_id", name="uq_subject_class"),
        Index("ix_subjects_school_class", "school_id", "class_id"),
    )


class TeacherSubjectMapping(BaseModel):
    """Maps a teacher to a subject in a class."""
    __tablename__ = "teacher_subject_mappings"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("teacher_id", "subject_id", "class_id", name="uq_teacher_subject_class"),
    )
