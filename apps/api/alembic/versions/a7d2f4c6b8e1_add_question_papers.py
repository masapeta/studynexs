"""add question_papers table

Revision ID: a7d2f4c6b8e1
Revises: f1c3a5b7d9e0
Create Date: 2026-05-31

Stores AI-drafted question papers (board/grade/subject/blueprint as data) plus the
teacher-edited/approved body. status gates the human-in-the-loop review.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a7d2f4c6b8e1"
down_revision: Union[str, None] = "f1c3a5b7d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_papers",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("board", sa.String(length=50), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("subject_name", sa.String(length=100), nullable=False),
        sa.Column("total_marks", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("difficulty_mix", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("general_instructions", sa.Text(), nullable=True),
        sa.Column("sections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "APPROVED", name="paperstatus"),
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
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_question_papers_school_class",
        "question_papers",
        ["school_id", "class_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_question_papers_school_class", table_name="question_papers")
    op.drop_table("question_papers")
    sa.Enum(name="paperstatus").drop(op.get_bind(), checkfirst=True)
