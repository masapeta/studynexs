"""Knowledge Graph: Student → weak Concept links (Batch 22).

Revision ID: c0d1e2f3a4b5
"""
from __future__ import annotations

from alembic import op

revision = "c0d1e2f3a4b5"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE kgnodetype ADD VALUE IF NOT EXISTS 'student'")
    op.execute("ALTER TYPE kgedgetype ADD VALUE IF NOT EXISTS 'struggles_with'")


def downgrade() -> None:
    op.execute("DELETE FROM kg_edges WHERE edge_type = 'struggles_with'")
