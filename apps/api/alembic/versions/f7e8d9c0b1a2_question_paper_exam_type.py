"""Persist the canonical examination type on question papers.

Revision ID: f7e8d9c0b1a2
Revises: a1b2c3d4e5f7
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f7e8d9c0b1a2"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Generic formative/summative categories are curriculum-neutral. Ordinals such as FA-I
    # and SA-II remain versioned curriculum/title data rather than enum values.
    op.execute("ALTER TYPE examtype ADD VALUE IF NOT EXISTS 'FORMATIVE_ASSESSMENT'")
    op.execute("ALTER TYPE examtype ADD VALUE IF NOT EXISTS 'SUMMATIVE_ASSESSMENT'")
    # The enum is the existing Exam.exam_type PostgreSQL type. Reusing it prevents paper and
    # examination vocabularies from drifting into two competing contracts.
    exam_type = postgresql.ENUM(
        "UNIT_TEST",
        "FORMATIVE_ASSESSMENT",
        "SUMMATIVE_ASSESSMENT",
        "MID_TERM",
        "FINAL",
        "ASSIGNMENT",
        "QUIZ",
        "SLIP_TEST",
        "QUARTERLY",
        "HALF_YEARLY",
        name="examtype",
        create_type=False,
    )
    op.add_column(
        "question_papers",
        sa.Column("ungrounded_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "question_papers",
        sa.Column(
            "exam_type",
            exam_type,
            nullable=False,
            server_default="UNIT_TEST",
        ),
    )


def downgrade() -> None:
    op.drop_column("question_papers", "ungrounded_reason")
    op.drop_column("question_papers", "exam_type")
    # PostgreSQL enum labels cannot be removed safely in place. As with the existing mastery
    # migration, the two generic labels remain harmless if this revision is downgraded.
