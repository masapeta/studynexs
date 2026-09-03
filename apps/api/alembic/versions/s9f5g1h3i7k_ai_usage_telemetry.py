"""AI usage telemetry columns — fallback routing and call status."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "s9f5g1h3i7k"
down_revision = "r8e4f0g2h6j"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("ai_usage"):
        return
    existing = {c["name"] for c in insp.get_columns("ai_usage")}

    if "status" not in existing:
        op.add_column(
            "ai_usage",
            sa.Column("status", sa.String(length=30), nullable=False, server_default="success"),
        )
    if "primary_provider" not in existing:
        op.add_column(
            "ai_usage",
            sa.Column("primary_provider", sa.String(length=50), nullable=True),
        )
    if "used_fallback" not in existing:
        op.add_column(
            "ai_usage",
            sa.Column("used_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    existing_indexes = {idx["name"] for idx in insp.get_indexes("ai_usage")}
    if "ix_ai_usage_status_created" not in existing_indexes:
        op.create_index(
            "ix_ai_usage_status_created",
            "ai_usage",
            ["status", "created_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("ai_usage"):
        return
    existing_indexes = {idx["name"] for idx in insp.get_indexes("ai_usage")}
    if "ix_ai_usage_status_created" in existing_indexes:
        op.drop_index("ix_ai_usage_status_created", table_name="ai_usage")

    existing = {c["name"] for c in insp.get_columns("ai_usage")}
    if "used_fallback" in existing:
        op.drop_column("ai_usage", "used_fallback")
    if "primary_provider" in existing:
        op.drop_column("ai_usage", "primary_provider")
    if "status" in existing:
        op.drop_column("ai_usage", "status")
