"""Teacher lesson plan — AI-drafted, human-approved before class use.

CurriculumPack integration comes later; chapter/topic are stored as snapshots today.
"""
from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class LessonPlanStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class LessonPlan(BaseModel):
    __tablename__ = "lesson_plans"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(150))
    topic: Mapped[str | None] = mapped_column(String(150))
    scheduled_for: Mapped[date | None] = mapped_column(Date)
    # [{duration_min, activity}]
    segments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[LessonPlanStatus] = mapped_column(
        Enum(LessonPlanStatus, values_callable=lambda x: [e.value for e in x]),
        default=LessonPlanStatus.DRAFT,
        nullable=False,
    )
    ai_model: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id"), nullable=True
    )
    grounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    grounding_sources: Mapped[list | None] = mapped_column(JSONB)
