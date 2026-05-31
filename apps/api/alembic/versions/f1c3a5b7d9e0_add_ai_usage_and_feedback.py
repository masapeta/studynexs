"""add ai_usage and ai_feedback tables

Revision ID: f1c3a5b7d9e0
Revises: e7b9c1d3f5a2
Create Date: 2026-05-31

Metering (tokens/cost/latency per LLM call) and quality feedback (thumbs up/down)
for the provider-agnostic AI gateway. Foundation for the cost benchmark + tuning.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f1c3a5b7d9e0"
down_revision: Union[str, None] = "e7b9c1d3f5a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("school_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("feature", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_usage_school_feature", "ai_usage", ["school_id", "feature"], unique=False
    )

    op.create_table(
        "ai_feedback",
        sa.Column("school_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("feature", sa.String(length=100), nullable=False),
        sa.Column("ref_type", sa.String(length=50), nullable=True),
        sa.Column("ref_id", sa.String(length=100), nullable=True),
        sa.Column("rating", sa.String(length=10), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_feedback_school_feature", "ai_feedback", ["school_id", "feature"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_ai_feedback_school_feature", table_name="ai_feedback")
    op.drop_table("ai_feedback")
    op.drop_index("ix_ai_usage_school_feature", table_name="ai_usage")
    op.drop_table("ai_usage")
