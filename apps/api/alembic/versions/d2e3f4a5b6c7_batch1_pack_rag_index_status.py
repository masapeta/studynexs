"""Batch 1 reconciliation: curriculum pack RAG indexing status.

Records when an approved pack was published into the curriculum knowledge layer and
surfaces indexing failures without blocking approval.

Revision ID: d2e3f4a5b6c7
Revises: c0d1e2f3a4b5
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "d2e3f4a5b6c7"
down_revision = "c0d1e2f3a4b5"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("curriculum_packs", "rag_indexed_at"):
        op.add_column(
            "curriculum_packs",
            sa.Column("rag_indexed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column("curriculum_packs", "rag_index_topic_count"):
        op.add_column(
            "curriculum_packs",
            sa.Column("rag_index_topic_count", sa.Integer(), nullable=True),
        )
    if not _has_column("curriculum_packs", "rag_index_error"):
        op.add_column(
            "curriculum_packs",
            sa.Column("rag_index_error", sa.String(length=500), nullable=True),
        )


def downgrade() -> None:
    if _has_column("curriculum_packs", "rag_index_error"):
        op.drop_column("curriculum_packs", "rag_index_error")
    if _has_column("curriculum_packs", "rag_index_topic_count"):
        op.drop_column("curriculum_packs", "rag_index_topic_count")
    if _has_column("curriculum_packs", "rag_indexed_at"):
        op.drop_column("curriculum_packs", "rag_indexed_at")
