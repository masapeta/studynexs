"""add report_cards table

Revision ID: b8e0d2f4a6c1
Revises: a7d2f4c6b8e1
Create Date: 2026-06-01

Consolidated report cards: subject-wise marks + attendance + an AI-drafted remark,
teacher-reviewed/approved. Attacks the school's stated #1 pain (report-card prep).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b8e0d2f4a6c1"
down_revision: Union[str, None] = "a7d2f4c6b8e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_cards",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("student_name", sa.String(length=200), nullable=False),
        sa.Column("class_name", sa.String(length=50), nullable=False),
        sa.Column("subjects", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("total_obtained", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("total_max", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("overall_grade", sa.String(length=5), nullable=True),
        sa.Column("attendance_percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("ai_remark", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "APPROVED", name="reportstatus"),
            nullable=False,
        ),
        sa.Column("ai_model", sa.String(length=100), nullable=True),
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
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_report_cards_school_class", "report_cards", ["school_id", "class_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_report_cards_school_class", table_name="report_cards")
    op.drop_table("report_cards")
    sa.Enum(name="reportstatus").drop(op.get_bind(), checkfirst=True)
