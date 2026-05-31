"""AI usage metering — one row per LLM call (tokens, cost, latency) for billing & analysis."""
from __future__ import annotations

import uuid

from sqlalchemy import Index, Integer, Numeric, String
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
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_ai_usage_school_feature", "school_id", "feature"),
    )
