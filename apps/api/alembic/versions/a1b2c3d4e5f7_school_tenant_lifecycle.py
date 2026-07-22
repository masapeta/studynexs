"""Stage 2B: school tenant lifecycle (kind, expiry, demo session).

Revision ID: a1b2c3d4e5f7
Revises: x9a8b7c6d5e4
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "a1b2c3d4e5f7"
down_revision = "x9a8b7c6d5e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "schools",
        sa.Column(
            "tenant_kind",
            sa.String(length=32),
            nullable=False,
            server_default="customer",
        ),
    )
    op.add_column(
        "schools",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "schools",
        sa.Column("provisioned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "schools",
        sa.Column("demo_session_token_hash", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_schools_tenant_kind", "schools", ["tenant_kind"])
    op.create_index("ix_schools_expires_at", "schools", ["expires_at"])
    op.create_index(
        "ix_schools_demo_session_token_hash",
        "schools",
        ["demo_session_token_hash"],
        unique=True,
    )

    op.execute(
        sa.text(
            "UPDATE schools SET tenant_kind = 'reference' WHERE tenant_slug = 'reference'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE schools SET tenant_kind = 'pilot' WHERE tenant_slug IN ('naagarjuna')"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_schools_demo_session_token_hash", table_name="schools")
    op.drop_index("ix_schools_expires_at", table_name="schools")
    op.drop_index("ix_schools_tenant_kind", table_name="schools")
    op.drop_column("schools", "demo_session_token_hash")
    op.drop_column("schools", "provisioned_at")
    op.drop_column("schools", "expires_at")
    op.drop_column("schools", "tenant_kind")
