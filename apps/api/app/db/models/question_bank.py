"""School-private question bank — atomic reusable items ingested on paper approval."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel

# Bank item approval states — string column (not PG enum) so draft/rejected can be added later
# without a migration. Ingest on paper approve only creates ``approved`` rows today.
BANK_STATUS_APPROVED = "approved"
BANK_APPROVAL_STATUSES = frozenset({BANK_STATUS_APPROVED})  # extend when bank has draft/rejected rows


class QuestionSource(str, enum.Enum):
    AI = "ai"
    TEACHER = "teacher"
    PREVIOUS_PAPER = "previous_paper"


class QuestionBankItem(BaseModel):
    """Atomic question extracted from an approved question paper."""

    __tablename__ = "question_bank_items"
    __table_args__ = (
        UniqueConstraint(
            "source_paper_id",
            "section_title",
            "question_number",
            name="uq_bank_item_paper_section_question",
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    source_paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    section_title: Mapped[str] = mapped_column(String(200), nullable=False)
    question_number: Mapped[str] = mapped_column(String(20), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False, default="short")
    options: Mapped[list | None] = mapped_column(JSONB)  # MCQ options

    board: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    topics: Mapped[list | None] = mapped_column(JSONB)

    source: Mapped[QuestionSource] = mapped_column(
        Enum(QuestionSource, values_callable=lambda x: [e.value for e in x]),
        default=QuestionSource.AI,
        nullable=False,
    )
    approval_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BANK_STATUS_APPROVED,
        server_default=BANK_STATUS_APPROVED,
    )
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    used_in_paper_ids: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    ai_model: Mapped[str | None] = mapped_column(String(100))


class RubricBankItem(BaseModel):
    """Marking scheme for a bank question — improves eval accuracy later."""

    __tablename__ = "rubric_bank_items"

    question_bank_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_bank_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    answer_key: Mapped[str | None] = mapped_column(Text)
    step_wise_marking: Mapped[list | None] = mapped_column(JSONB)
    acceptable_answers: Mapped[list | None] = mapped_column(JSONB)
    common_wrong_answers: Mapped[list | None] = mapped_column(JSONB)
    teacher_correction_note: Mapped[str | None] = mapped_column(Text)
