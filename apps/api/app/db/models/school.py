"""School (tenant) model — the root entity for multi-tenancy."""
from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class School(BaseModel):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    tenant_slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    board: Mapped[str | None] = mapped_column(String(50))  # CBSE, ICSE, State Board
    address: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    enabled_modules: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    subscription: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(15))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Stage 2B — prospect demo lifecycle (customer | reference | pilot | prospect_demo)
    tenant_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="customer")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provisioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    demo_session_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)

    @property
    def theme_color(self) -> str | None:
        """School's brand accent colour (hex) for per-tenant theming; lives in settings."""
        return (self.settings or {}).get("theme_color")
