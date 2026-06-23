"""AI credit metering columns + QP approval audit.

Revision ID: g7b3c9d1e2f4
Revises: f6a2b8c4d0e5
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "g7b3c9d1e2f4"
down_revision = "f6a2b8c4d0e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_usage", sa.Column("role", sa.String(length=30), nullable=True))
    op.add_column("ai_usage", sa.Column("purpose_tag", sa.String(length=50), nullable=True))
    op.add_column(
        "ai_usage",
        sa.Column("credits_charged", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("ai_usage", sa.Column("ref_type", sa.String(length=50), nullable=True))
    op.add_column("ai_usage", sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "ai_usage",
        sa.Column("image_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_ai_usage_school_purpose", "ai_usage", ["school_id", "purpose_tag"])

    op.add_column(
        "question_papers",
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "question_papers",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_question_papers_approved_by",
        "question_papers",
        "users",
        ["approved_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_question_papers_approved_by", "question_papers", type_="foreignkey")
    op.drop_column("question_papers", "approved_at")
    op.drop_column("question_papers", "approved_by")
    op.drop_index("ix_ai_usage_school_purpose", table_name="ai_usage")
    op.drop_column("ai_usage", "image_count")
    op.drop_column("ai_usage", "ref_id")
    op.drop_column("ai_usage", "ref_type")
    op.drop_column("ai_usage", "credits_charged")
    op.drop_column("ai_usage", "purpose_tag")
    op.drop_column("ai_usage", "role")
