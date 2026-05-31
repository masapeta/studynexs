"""School (tenant) model — the root entity for multi-tenancy."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String, Text
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
