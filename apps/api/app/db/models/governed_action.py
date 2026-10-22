"""Governed action execution ledger — server-side idempotency for stateless state-changing
actions (e.g. publish_notice).

Unlike a workflow that persists a domain draft (parent intervention idempotency-guards on a
domain unique key), a stateless action has no natural dedupe key — and a school may legitimately
publish identical content more than once. So the confirmation carries a server-issued
`action_token`; this ledger records one row per confirmed execution. A retry/double-click with the
SAME token is idempotent (returns the recorded result); a fresh preview mints a NEW token and may
legitimately execute again.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel

ACTION_STATUS_COMPLETED = "completed"
ACTION_STATUS_FAILED = "failed"


class GovernedActionExecution(BaseModel):
    """One confirmed execution of a governed assistant action, keyed by its confirmation token."""

    __tablename__ = "governed_action_executions"
    __table_args__ = (
        # Idempotency: one execution per (school, token). A retried confirmation collides here.
        UniqueConstraint("school_id", "action_token", name="uq_governed_action_token"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. "publish_notice"
    action_token: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ACTION_STATUS_COMPLETED)
    # The domain object created by the action (e.g. the notice id), for idempotent replay.
    result_type: Mapped[str | None] = mapped_column(String(60))
    result_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    error_message: Mapped[str | None] = mapped_column(Text)
