"""AI feedback — thumbs up/down (+ optional note) on AI outputs, for quality tracking."""
from __future__ import annotations

import uuid

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class AIFeedback(BaseModel):
    __tablename__ = "ai_feedback"

    school_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    ref_type: Mapped[str | None] = mapped_column(String(50))  # e.g. "question_paper", "exam_mark"
    ref_id: Mapped[str | None] = mapped_column(String(100))
    rating: Mapped[str] = mapped_column(String(10), nullable=False)  # "up" | "down"
    note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_ai_feedback_school_feature", "school_id", "feature"),
    )
