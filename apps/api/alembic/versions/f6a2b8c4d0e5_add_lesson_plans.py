"""Add lesson_plans table.

Revision ID: f6a2b8c4d0e5
Revises: e5f9a1b3c7d4
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f6a2b8c4d0e5"
down_revision = "e5f9a1b3c7d4"
branch_labels = None
depends_on = None

_STATUS = postgresql.ENUM("draft", "approved", name="lessonplanstatus", create_type=False)


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE lessonplanstatus AS ENUM ('draft', 'approved'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.create_table(
        "lesson_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("chapter", sa.String(length=150), nullable=True),
        sa.Column("topic", sa.String(length=150), nullable=True),
        sa.Column("scheduled_for", sa.Date(), nullable=True),
        sa.Column("segments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", _STATUS, nullable=False),
        sa.Column("ai_model", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lesson_plans_school_class_subject", "lesson_plans", ["school_id", "class_id", "subject_id"])


def downgrade() -> None:
    op.drop_index("ix_lesson_plans_school_class_subject", table_name="lesson_plans")
    op.drop_table("lesson_plans")
    op.execute("DROP TYPE IF EXISTS lessonplanstatus")
