"""Add notice audience (internal vs external).

Revision ID: e5f9a1b3c7d4
Revises: d4e8f0a2b6c3
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e5f9a1b3c7d4"
down_revision = "d4e8f0a2b6c3"
branch_labels = None
depends_on = None

_AUDIENCE = sa.Enum("internal", "external", name="noticeaudience")


def upgrade() -> None:
    _AUDIENCE.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "notices",
        sa.Column(
            "audience",
            _AUDIENCE,
            nullable=False,
            server_default="external",
        ),
    )
    op.alter_column("notices", "audience", server_default=None)


def downgrade() -> None:
    op.drop_column("notices", "audience")
    _AUDIENCE.drop(op.get_bind(), checkfirst=True)
