"""report card exam manifest for learner read path (P2 Stage 2)

Revision ID: r7e3a9c5d2b8
Revises: r6d2f8b4a1c9
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "r7e3a9c5d2b8"
down_revision = "r6d2f8b4a1c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "report_cards",
        sa.Column("exam_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("report_cards", "exam_ids")
