"""governed action executions (idempotency ledger)

Revision ID: p5c2e9f3b7d4
Revises: n4b1d8e2a6c3
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "p5c2e9f3b7d4"
down_revision = "n4b1d8e2a6c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "governed_action_executions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column("action_token", sa.UUID(), nullable=False),
        sa.Column("initiated_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("result_type", sa.String(length=60), nullable=True),
        sa.Column("result_id", sa.UUID(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=True),
    )
    op.create_unique_constraint(
        "uq_governed_action_token", "governed_action_executions",
        ["school_id", "action_token"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_governed_action_token", "governed_action_executions", type_="unique"
    )
    op.drop_table("governed_action_executions")
