"""ConceptCard table — tutor grounding unit (Batch 18).

Revision ID: z6a7b8c9d0e1
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "z6a7b8c9d0e1"
down_revision = "y5f6a7b8c9d0"
branch_labels = None
depends_on = None

_card_status = postgresql.ENUM("draft", "approved", name="conceptcardstatus", create_type=False)


def upgrade() -> None:
    _card_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "concept_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("examples", postgresql.JSONB(), nullable=True),
        sa.Column("hints", postgresql.JSONB(), nullable=True),
        sa.Column("visual_kind", sa.String(50), nullable=False, server_default="generic"),
        sa.Column("status", _card_status, nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["concept_id"], ["curriculum_concepts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "concept_id", name="uq_concept_card_per_concept"),
    )
    op.create_index(
        "ix_concept_cards_school_pack", "concept_cards", ["school_id", "pack_id"]
    )
    op.create_index("ix_concept_cards_concept", "concept_cards", ["concept_id"])


def downgrade() -> None:
    op.drop_index("ix_concept_cards_concept", table_name="concept_cards")
    op.drop_index("ix_concept_cards_school_pack", table_name="concept_cards")
    op.drop_table("concept_cards")
    _card_status.drop(op.get_bind(), checkfirst=True)
