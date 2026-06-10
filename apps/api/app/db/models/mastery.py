"""Mastery models — per-student per-topic mastery ledger + weakness flags.

The ledger is the durable data asset behind weakness alerts, parent digests and
targeted practice generation. Detection is deterministic (no LLM in the math path);
flags carry frozen evidence so the narrative a teacher approves is grounded in
exactly the facts that raised the flag.
"""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class MasteryTrend(str, enum.Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT = "insufficient"  # fewer than 2 datapoints — never flagged


class StudentTopicMastery(BaseModel):
    __tablename__ = "student_topic_mastery"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    # Snapshot of the student's class at last recompute (students can move sections).
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    # Normalized aggregation key (trim/casefold) vs original casing for display.
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    topic_display: Mapped[str] = mapped_column(String(120), nullable=False)
    # Weighted by exam type, recency-decayed (half-life 90 days).
    mastery_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    # Class average for the same topic, snapshotted in the same recompute pass.
    class_avg_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    assessments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_assessed_on: Mapped[date | None] = mapped_column(Date)
    trend: Mapped[MasteryTrend] = mapped_column(
        Enum(MasteryTrend), nullable=False, default=MasteryTrend.INSUFFICIENT
    )
    # Last 8 datapoints: [{"exam_id", "date", "pct", "weight", "exam_type"}] —
    # makes every number explainable in the UI and is the LLM grounding payload.
    history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_id", "academic_year_id", "topic",
            name="uq_student_topic_mastery",
        ),
        Index("ix_stm_school_student", "school_id", "student_id"),
        Index("ix_stm_school_class_subject", "school_id", "class_id", "subject_id", "topic"),
    )


class FlagSeverity(str, enum.Enum):
    MEDIUM = "medium"
    HIGH = "high"


class FlagStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"  # teacher approved; LLM narrative drafted, editable
    DISMISSED = "dismissed"
    NOTIFIED = "notified"  # narrative sent to linked parent users


class MasteryFlag(BaseModel):
    __tablename__ = "mastery_flags"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    topic_display: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[FlagSeverity] = mapped_column(Enum(FlagSeverity), nullable=False)
    status: Mapped[FlagStatus] = mapped_column(
        Enum(FlagStatus), nullable=False, default=FlagStatus.PENDING_REVIEW
    )
    # Rule names that fired: ["below_class_avg", "declining_trend", "absolute_floor"]
    reasons: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Facts frozen at raise time (scores, class avg, trend, history) — what the
    # teacher approves and the only material the LLM may draw on.
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    narrative: Mapped[str | None] = mapped_column(Text)
    ai_model: Mapped[str | None] = mapped_column(String(100))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dismissed_reason: Mapped[str | None] = mapped_column(String(300))
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # At most one OPEN flag per student+subject+year+topic — makes concurrent
        # flag-raising race-safe and idempotent (insert with ON CONFLICT DO NOTHING).
        Index(
            "uq_open_flag_per_topic",
            "student_id", "subject_id", "academic_year_id", "topic",
            unique=True,
            postgresql_where=text("status = 'PENDING_REVIEW'"),
        ),
        Index("ix_mastery_flags_school_status", "school_id", "status"),
        Index("ix_mastery_flags_school_student", "school_id", "student_id"),
    )
