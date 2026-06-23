"""Misconception library — teaching memory from answer-sheet evaluation."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class MisconceptionEntry(BaseModel):
    """School-private common mistake + remedial hint, tagged by topic/concept."""

    __tablename__ = "misconception_entries"
    __table_args__ = (
        UniqueConstraint("school_id", "content_fingerprint", name="uq_misconception_fingerprint"),
        Index("ix_misconception_school_topic", "school_id", "topic"),
        Index("ix_misconception_school_class", "school_id", "class_id"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    question_no: Mapped[str | None] = mapped_column(String(20))
    common_mistake: Mapped[str] = mapped_column(Text, nullable=False)
    remedial_activity: Mapped[str | None] = mapped_column(Text)
    source_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answer_sheet_evaluations.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
