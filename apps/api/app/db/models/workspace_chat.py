"""Persistent chat sessions and messages for the command workspace.

Gives the assistant durable history (list past conversations) and session memory
(prior turns in a conversation) so follow-up questions can be answered in context.
Both tables are tenant-scoped by school_id and owned by a user.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class WorkspaceChatSession(BaseModel):
    """One chat conversation for a user within a school (tenant-scoped)."""

    __tablename__ = "workspace_chat_sessions"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="New chat")
    # Reversible archive (P3): hidden from the default list, restorable; never hard-deleted.
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list["WorkspaceChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkspaceChatMessage.created_at",
    )

    __table_args__ = (
        Index("ix_workspace_chat_sessions_school_user", "school_id", "user_id"),
        Index(
            "ix_workspace_chat_sessions_owner_archived", "school_id", "user_id", "archived_at"
        ),
    )


class WorkspaceChatMessage(BaseModel):
    """A single message in a chat session: user prompt or assistant response.

    `role` is "user" or "assistant". `result_kind` records how the assistant
    answered (navigate/data/table/query/guide) so history + follow-ups stay
    contextual. `payload` holds a small, non-authoritative snapshot for redisplay.
    """

    __tablename__ = "workspace_chat_messages"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspace_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Compact structured semantic state after this turn (domain/entity/operation/temporal)
    # so an elliptical follow-up can inherit unchanged dimensions (P1.2). Never authoritative
    # and never an authorization token — every turn re-checks permissions.
    semantic_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    session: Mapped[WorkspaceChatSession] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_workspace_chat_messages_session", "session_id", "created_at"),
    )
