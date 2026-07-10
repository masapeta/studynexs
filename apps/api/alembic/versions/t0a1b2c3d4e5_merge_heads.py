"""Merge the two open migration heads into one.

The chain had forked into two parallel heads (eval-vision-misconception + ai-usage-telemetry),
which makes ``alembic upgrade head`` ambiguous. This is an empty merge point that unifies them;
no schema changes here.

Revision ID: t0a1b2c3d4e5
"""
from __future__ import annotations

revision = "t0a1b2c3d4e5"
down_revision = ("l2f8g4b6c0d", "s9f5g1h3i7k")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
