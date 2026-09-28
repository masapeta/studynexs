"""Parent intervention — a 1:1 draft message to a parent, sent only after human approval.

Persisted so the governed action (approve & notify) can re-validate, be idempotent, and be
audited at approval time — a stateless chat draft cannot be idempotency-guarded. Each row is a
single parent↔student intervention (strictly 1:1; never a bulk notification).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel

INTERVENTION_STATUS_DRAFT = "draft"        # generated, awaiting human approval
INTERVENTION_STATUS_NOTIFIED = "notified"  # approved + IN_APP notification created
INTERVENTION_STATUS_FAILED = "failed"      # approval attempted but delivery failed


class ParentInterventionBatch(BaseModel):
    """One workflow run: the cohort of 1:1 drafts produced together."""

    __tablename__ = "parent_intervention_batches"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. "low_attendance"

    __table_args__ = (Index("ix_parent_intervention_batch_school", "school_id"),)


class ParentInterventionDraft(BaseModel):
    """A single 1:1 parent message draft within a batch."""

    __tablename__ = "parent_intervention_drafts"
    __table_args__ = (
        # Idempotency: one delivered draft per (batch, student, parent). Re-approval of the same
        # draft row is guarded in-service; this prevents duplicate rows for the same target.
        UniqueConstraint(
            "batch_id", "student_id", "parent_user_id",
            name="uq_intervention_batch_student_parent",
        ),
        Index("ix_intervention_draft_school_status", "school_id", "status"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parent_intervention_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    parent_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(60), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=INTERVENTION_STATUS_DRAFT
    )
    notification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
