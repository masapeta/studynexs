"""workspace chat message semantic_state (conversational carry-over, P1.2)

Revision ID: m3a9c2e7f1b0
Revises: b7f2c1a9d3e5
Create Date: 2026-09-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "m3a9c2e7f1b0"
down_revision: Union[str, None] = "b7f2c1a9d3e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workspace_chat_messages",
        sa.Column("semantic_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workspace_chat_messages", "semantic_state")
