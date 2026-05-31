"""Audit log — append-only, immutable record of sensitive actions."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True  # NULL for platform-level actions
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(50))
    details: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(300))

    __table_args__ = (
        Index("ix_audit_school_action", "school_id", "action"),
        Index("ix_audit_user", "user_id"),
    )
