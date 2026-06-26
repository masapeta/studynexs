"""curriculum packs: versioned syllabus (pack -> chapter -> topic)

Revision ID: m3f9a5c7b1d
Revises: l2f8g4b6c0d
Create Date: 2026-06-23

The structured-curriculum moat. A CurriculumPack (per school×class×subject×year×
edition) holds a chapter→topic tree + exam blueprint; drafts are editable, approved
packs are immutable (change = new version). All additive — nothing existing touched.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "m3f9a5c7b1d"
down_revision: Union[str, None] = "l2f8g4b6c0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "curriculum_packs",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=False),
        sa.Column("board", sa.String(length=50), nullable=False),
        sa.Column("book_title", sa.String(length=200), nullable=True),
        sa.Column("publisher", sa.String(length=150), nullable=True),
        sa.Column("edition", sa.String(length=50), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "APPROVED", name="packstatus"), nullable=False),
        sa.Column("blueprint", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id", "class_id", "subject_id", "academic_year_id", "version",
            name="uq_pack_scope_version",
        ),
    )
    op.create_index("ix_packs_school_scope", "curriculum_packs", ["school_id", "class_id", "subject_id", "academic_year_id"])

    op.create_table(
        "curriculum_chapters",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("pack_id", sa.UUID(), nullable=False),
        sa.Column("number", sa.String(length=20), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chapters_pack", "curriculum_chapters", ["pack_id"])

    op.create_table(
        "curriculum_topics",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("chapter_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("concepts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["chapter_id"], ["curriculum_chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topics_chapter", "curriculum_topics", ["chapter_id"])


def downgrade() -> None:
    op.drop_index("ix_topics_chapter", table_name="curriculum_topics")
    op.drop_table("curriculum_topics")
    op.drop_index("ix_chapters_pack", table_name="curriculum_chapters")
    op.drop_table("curriculum_chapters")
    op.drop_index("ix_packs_school_scope", table_name="curriculum_packs")
    op.drop_table("curriculum_packs")
    sa.Enum(name="packstatus").drop(op.get_bind(), checkfirst=True)
