"""Content Review Queue table (Batch 20).

Revision ID: b9c0d1e2f3a4
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None

_item_type = postgresql.ENUM(
    "concept_card_gap", "document_ingest", name="contentreviewitemtype", create_type=False
)
_status = postgresql.ENUM(
    "pending", "approved", "rejected", name="contentreviewstatus", create_type=False
)
_source = postgresql.ENUM(
    "tutor_gap", "document_ingest", "teacher", name="contentreviewsource", create_type=False
)


def upgrade() -> None:
    _item_type.create(op.get_bind(), checkfirst=True)
    _status.create(op.get_bind(), checkfirst=True)
    _source.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "content_review_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", _item_type, nullable=False),
        sa.Column("status", _status, nullable=False, server_default="pending"),
        sa.Column("source", _source, nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("draft_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("result_card_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["concept_id"], ["curriculum_concepts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["result_card_id"], ["concept_cards.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_review_school_pack_status",
        "content_review_items",
        ["school_id", "pack_id", "status"],
    )
    op.create_index(
        "ix_content_review_concept",
        "content_review_items",
        ["school_id", "concept_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_content_review_concept", table_name="content_review_items")
    op.drop_index("ix_content_review_school_pack_status", table_name="content_review_items")
    op.drop_table("content_review_items")
    _source.drop(op.get_bind(), checkfirst=True)
    _status.drop(op.get_bind(), checkfirst=True)
    _item_type.drop(op.get_bind(), checkfirst=True)
