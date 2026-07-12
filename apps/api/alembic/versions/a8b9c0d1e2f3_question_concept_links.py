"""Knowledge Graph: Question → Concept links (Batch 19).

Revision ID: a8b9c0d1e2f3
"""
from __future__ import annotations

from alembic import op

revision = "a8b9c0d1e2f3"
down_revision = "z6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE kgnodetype ADD VALUE IF NOT EXISTS 'question_bank_item'"
    )
    op.execute("ALTER TYPE kgedgetype ADD VALUE IF NOT EXISTS 'tests'")
    op.create_index(
        "ix_kg_edges_from",
        "kg_edges",
        ["school_id", "from_node_type", "from_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_kg_edges_from", table_name="kg_edges")
    op.execute("DELETE FROM kg_edges WHERE edge_type = 'tests'")
    # PostgreSQL cannot remove enum values; leave extended types in place.
