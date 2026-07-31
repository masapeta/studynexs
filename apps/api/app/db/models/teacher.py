"""Teacher model — extends User with professional details.

CONVENTION: scheduling/authorization tables (timetable_slots.teacher_id,
teacher_subject_mappings.teacher_id, classes.class_incharge_id) FK to
``users.id`` — NOT to this table. ``teachers`` is an HR/profile extension of
the user row. Do not add FKs to teachers.id for academic workflows.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class Teacher(BaseModel):
    __tablename__ = "teachers"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    employee_id: Mapped[str | None] = mapped_column(String(50))
    qualification: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(String(100))
    joining_date: Mapped[date | None] = mapped_column(Date)

    # Relationships
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("ix_teachers_school", "school_id"),
    )
