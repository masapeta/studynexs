"""Batch 1 reconciliation: curriculum learning outcomes.

First-class learning outcomes scoped to a topic or chapter within a CurriculumPack.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "e3f4a5b6c7d8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    if _has_table("curriculum_learning_outcomes"):
        return
    op.create_table(
        "curriculum_learning_outcomes",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("topic_id", sa.UUID(), nullable=True),
        sa.Column("chapter_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["curriculum_topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["curriculum_chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(topic_id IS NOT NULL AND chapter_id IS NULL) OR "
            "(topic_id IS NULL AND chapter_id IS NOT NULL)",
            name="ck_learning_outcome_topic_xor_chapter",
        ),
    )
    op.create_index(
        "ix_learning_outcomes_topic",
        "curriculum_learning_outcomes",
        ["topic_id"],
    )
    op.create_index(
        "ix_learning_outcomes_chapter",
        "curriculum_learning_outcomes",
        ["chapter_id"],
    )


def downgrade() -> None:
    if not _has_table("curriculum_learning_outcomes"):
        return
    op.drop_index("ix_learning_outcomes_chapter", table_name="curriculum_learning_outcomes")
    op.drop_index("ix_learning_outcomes_topic", table_name="curriculum_learning_outcomes")
    op.drop_table("curriculum_learning_outcomes")
