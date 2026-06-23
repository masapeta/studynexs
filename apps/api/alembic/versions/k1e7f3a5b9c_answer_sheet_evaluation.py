"""Answer sheet evaluation v1 — exam source_paper_id + evaluations table.

Revision ID: k1e7f3a5b9c
Revises: j0d6e2f4a8b
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "k1e7f3a5b9c"
down_revision = "j0d6e2f4a8b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exams",
        sa.Column("source_paper_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_exams_source_paper_id",
        "exams",
        "question_papers",
        ["source_paper_id"],
        ["id"],
    )

    op.create_table(
        "answer_sheet_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("ai_suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correction_summary", sa.Text(), nullable=True),
        sa.Column("teacher_overrides", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_eval_exam_student"),
    )
    op.create_index("ix_eval_school_exam", "answer_sheet_evaluations", ["school_id", "exam_id"])
    op.create_index("ix_eval_school_status", "answer_sheet_evaluations", ["school_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_eval_school_status", table_name="answer_sheet_evaluations")
    op.drop_index("ix_eval_school_exam", table_name="answer_sheet_evaluations")
    op.drop_table("answer_sheet_evaluations")
    op.drop_constraint("fk_exams_source_paper_id", "exams", type_="foreignkey")
    op.drop_column("exams", "source_paper_id")
