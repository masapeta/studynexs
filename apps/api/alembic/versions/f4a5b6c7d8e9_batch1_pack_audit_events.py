"""Batch 1 reconciliation: curriculum pack audit events.

Append-only audit trail for CurriculumPack lifecycle (create, edit, approve, RAG index).

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    if _has_table("curriculum_pack_audit_events"):
        return
    op.create_table(
        "curriculum_pack_audit_events",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("pack_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pack_audit_school_pack",
        "curriculum_pack_audit_events",
        ["school_id", "pack_id"],
    )
    op.create_index(
        "ix_pack_audit_pack_created",
        "curriculum_pack_audit_events",
        ["pack_id", "created_at"],
    )


def downgrade() -> None:
    if not _has_table("curriculum_pack_audit_events"):
        return
    op.drop_index("ix_pack_audit_pack_created", table_name="curriculum_pack_audit_events")
    op.drop_index("ix_pack_audit_school_pack", table_name="curriculum_pack_audit_events")
    op.drop_table("curriculum_pack_audit_events")
