"""Communication models — Notices with read receipts."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class NoticePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NoticeAudience(str, enum.Enum):
    """Who the notice is for — staff circulars vs parent/student communications."""
    INTERNAL = "internal"   # staff-only (admin, incharges, teachers)
    EXTERNAL = "external"  # students / parents


class Notice(BaseModel):
    __tablename__ = "notices"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_roles: Mapped[dict] = mapped_column(JSONB, nullable=False)  # role slugs
    audience: Mapped[NoticeAudience] = mapped_column(
        Enum(NoticeAudience, values_callable=lambda x: [e.value for e in x]),
        default=NoticeAudience.EXTERNAL,
        nullable=False,
    )
    priority: Mapped[NoticePriority] = mapped_column(
        Enum(NoticePriority),
        default=NoticePriority.MEDIUM,
    )
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # When set, notice is class-scoped (published by class incharge). Null = school-wide.
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NoticeReadReceipt(BaseModel):
    __tablename__ = "notice_read_receipts"

    notice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notices.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("notice_id", "user_id", name="uq_notice_read"),
    )
