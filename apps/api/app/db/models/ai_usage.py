"""AI usage metering — one row per LLM call (tokens, cost, latency) for billing & analysis."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class AIUsage(BaseModel):
    __tablename__ = "ai_usage"

    school_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    feature: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "question_paper"
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # gemini | anthropic | openai
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("0.000000"), nullable=False
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Credit metering — schools see credits, operators see cost_usd
    role: Mapped[str | None] = mapped_column(String(30))
    purpose_tag: Mapped[str | None] = mapped_column(String(50))
    credits_charged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ref_type: Mapped[str | None] = mapped_column(String(50))
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    image_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Telemetry — provider routing and call outcome
    status: Mapped[str] = mapped_column(String(30), default="success", nullable=False)
    primary_provider: Mapped[str | None] = mapped_column(String(50))
    used_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_ai_usage_school_feature", "school_id", "feature"),
        Index("ix_ai_usage_school_purpose", "school_id", "purpose_tag"),
        Index("ix_ai_usage_status_created", "status", "created_at"),
    )
