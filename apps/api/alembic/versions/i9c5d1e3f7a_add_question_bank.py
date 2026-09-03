"""Add question_bank_items and rubric_bank_items tables.

Revision ID: i9c5d1e3f7a
Revises: h8c4d0e2f6
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "i9c5d1e3f7a"
down_revision = "h8c4d0e2f6"
branch_labels = None
depends_on = None

_QUESTION_SOURCE = postgresql.ENUM(
    "ai", "teacher", "previous_paper", name="questionsource", create_type=False
)


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE questionsource AS ENUM ('ai', 'teacher', 'previous_paper'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.create_table(
        "question_bank_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("section_title", sa.String(length=200), nullable=False),
        sa.Column("question_number", sa.String(length=20), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("marks", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("board", sa.String(length=50), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", _QUESTION_SOURCE, nullable=False),
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
        sa.Column("content_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "used_in_paper_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("ai_model", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["source_paper_id"], ["question_papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_paper_id", "section_title", "question_number",
            name="uq_bank_item_paper_section_question",
        ),
    )
    op.create_index(
        "ix_bank_items_school_class_subject",
        "question_bank_items",
        ["school_id", "class_id", "subject_id"],
    )
    op.create_index(
        "ix_bank_items_fingerprint",
        "question_bank_items",
        ["school_id", "subject_id", "content_fingerprint"],
    )
    op.create_table(
        "rubric_bank_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("question_bank_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_key", sa.Text(), nullable=True),
        sa.Column("step_wise_marking", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("acceptable_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("common_wrong_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("teacher_correction_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["question_bank_item_id"], ["question_bank_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_bank_item_id"),
    )


def downgrade() -> None:
    op.drop_table("rubric_bank_items")
    op.drop_index("ix_bank_items_fingerprint", table_name="question_bank_items")
    op.drop_index("ix_bank_items_school_class_subject", table_name="question_bank_items")
    op.drop_table("question_bank_items")
    op.execute("DROP TYPE IF EXISTS questionsource")
