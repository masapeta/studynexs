"""report cards: not_assessed subjects column

Revision ID: f3c7b9d1a2e6
Revises: e2b5a7c9f1d4
Create Date: 2026-06-01

Surfaces subjects the class was examined in but a student has no marks for, so a missing
subject isn't silently dropped from the consolidated card. JSONB list of subject names,
NOT NULL defaulting to [] so existing rows backfill cleanly.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f3c7b9d1a2e6"
down_revision: Union[str, None] = "e2b5a7c9f1d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "report_cards",
        sa.Column(
            "not_assessed",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("report_cards", "not_assessed")
