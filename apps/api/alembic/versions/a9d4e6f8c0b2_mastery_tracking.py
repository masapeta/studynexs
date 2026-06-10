"""mastery tracking: SSC exam types, per-question marks, topic ledger + flags

Revision ID: a9d4e6f8c0b2
Revises: f3c7b9d1a2e6
Create Date: 2026-06-10

Foundations for per-student topic mastery tracking:
- examtype enum gains SSC terms (slip test, quarterly, half-yearly)
- exams carry an optional whole-exam topic tag and a per-question schema
  (no/max_marks/topic) — the source of truth for topic attribution
- exam_marks gain optional per-question marks (JSONB {qno: marks})
- student_topic_mastery: durable weighted ledger per student+subject+year+topic
- mastery_flags: weakness flags with frozen evidence, teacher review lifecycle

All changes additive/nullable — existing exams and marks are untouched.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a9d4e6f8c0b2"
down_revision: Union[str, None] = "f3c7b9d1a2e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PG ≥12 allows ADD VALUE inside a transaction as long as the new value is
    # not used in the same transaction (we only add it here).
    op.execute("ALTER TYPE examtype ADD VALUE IF NOT EXISTS 'SLIP_TEST'")
    op.execute("ALTER TYPE examtype ADD VALUE IF NOT EXISTS 'QUARTERLY'")
    op.execute("ALTER TYPE examtype ADD VALUE IF NOT EXISTS 'HALF_YEARLY'")

    op.add_column("exams", sa.Column("topic", sa.String(length=120), nullable=True))
    op.add_column(
        "exams",
        sa.Column("question_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "exam_marks",
        sa.Column("question_marks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "student_topic_mastery",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=False),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("topic_display", sa.String(length=120), nullable=False),
        sa.Column("mastery_pct", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("class_avg_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("assessments_count", sa.Integer(), nullable=False),
        sa.Column("last_assessed_on", sa.Date(), nullable=True),
        sa.Column(
            "trend",
            sa.Enum("IMPROVING", "STABLE", "DECLINING", "INSUFFICIENT", name="masterytrend"),
            nullable=False,
        ),
        sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id", "subject_id", "academic_year_id", "topic",
            name="uq_student_topic_mastery",
        ),
    )
    op.create_index(
        "ix_stm_school_student", "student_topic_mastery", ["school_id", "student_id"]
    )
    op.create_index(
        "ix_stm_school_class_subject",
        "student_topic_mastery",
        ["school_id", "class_id", "subject_id", "topic"],
    )

    op.create_table(
        "mastery_flags",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=False),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("topic_display", sa.String(length=120), nullable=False),
        sa.Column("severity", sa.Enum("MEDIUM", "HIGH", name="flagseverity"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING_REVIEW", "APPROVED", "DISMISSED", "NOTIFIED", name="flagstatus"),
            nullable=False,
        ),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("ai_model", sa.String(length=100), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_reason", sa.String(length=300), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_open_flag_per_topic",
        "mastery_flags",
        ["student_id", "subject_id", "academic_year_id", "topic"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING_REVIEW'"),
    )
    op.create_index("ix_mastery_flags_school_status", "mastery_flags", ["school_id", "status"])
    op.create_index("ix_mastery_flags_school_student", "mastery_flags", ["school_id", "student_id"])


def downgrade() -> None:
    op.drop_index("ix_mastery_flags_school_student", table_name="mastery_flags")
    op.drop_index("ix_mastery_flags_school_status", table_name="mastery_flags")
    op.drop_index("uq_open_flag_per_topic", table_name="mastery_flags")
    op.drop_table("mastery_flags")
    sa.Enum(name="flagstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="flagseverity").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_stm_school_class_subject", table_name="student_topic_mastery")
    op.drop_index("ix_stm_school_student", table_name="student_topic_mastery")
    op.drop_table("student_topic_mastery")
    sa.Enum(name="masterytrend").drop(op.get_bind(), checkfirst=True)

    op.drop_column("exam_marks", "question_marks")
    op.drop_column("exams", "question_schema")
    op.drop_column("exams", "topic")
    # NOTE: Postgres cannot remove enum values — SLIP_TEST/QUARTERLY/HALF_YEARLY
    # remain on examtype as harmless orphan labels.
