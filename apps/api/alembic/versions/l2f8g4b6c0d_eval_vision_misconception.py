"""Eval vision async + misconception library.

Revision ID: l2f8g4b6c0d
Revises: k1e7f3a5b9c
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "l2f8g4b6c0d"
down_revision = "k1e7f3a5b9c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE filecategory ADD VALUE IF NOT EXISTS 'ANSWER_SHEET'")

    op.add_column(
        "answer_sheet_evaluations",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "answer_sheet_evaluations",
        sa.Column("input_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_foreign_key(
        "fk_eval_job_id",
        "answer_sheet_evaluations",
        "jobs",
        ["job_id"],
        ["id"],
    )

    op.create_table(
        "misconception_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("question_no", sa.String(length=20), nullable=True),
        sa.Column("common_mistake", sa.Text(), nullable=False),
        sa.Column("remedial_activity", sa.Text(), nullable=True),
        sa.Column("source_evaluation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["source_evaluation_id"], ["answer_sheet_evaluations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "content_fingerprint", name="uq_misconception_fingerprint"),
    )
    op.create_index("ix_misconception_school_topic", "misconception_entries", ["school_id", "topic"])
    op.create_index("ix_misconception_school_class", "misconception_entries", ["school_id", "class_id"])


def downgrade() -> None:
    op.drop_index("ix_misconception_school_class", table_name="misconception_entries")
    op.drop_index("ix_misconception_school_topic", table_name="misconception_entries")
    op.drop_table("misconception_entries")
    op.drop_constraint("fk_eval_job_id", "answer_sheet_evaluations", type_="foreignkey")
    op.drop_column("answer_sheet_evaluations", "input_answers")
    op.drop_column("answer_sheet_evaluations", "job_id")
