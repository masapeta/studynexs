"""chat session reversible archive (P2 M6, decision P3)

Revision ID: r6d2f8b4a1c9
Revises: r5c9e1a3d7f4
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "r6d2f8b4a1c9"
down_revision = "r5c9e1a3d7f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspace_chat_sessions",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_workspace_chat_sessions_owner_archived",
        "workspace_chat_sessions",
        ["school_id", "user_id", "archived_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspace_chat_sessions_owner_archived", table_name="workspace_chat_sessions"
    )
    op.drop_column("workspace_chat_sessions", "archived_at")
