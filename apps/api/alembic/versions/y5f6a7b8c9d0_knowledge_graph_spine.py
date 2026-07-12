"""Knowledge Graph: curriculum spine tables (Batch 17).

Revision ID: y5f6a7b8c9d0
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "y5f6a7b8c9d0"
down_revision = "x4e5f6a7b8c9"
branch_labels = None
depends_on = None

_concept_source = postgresql.ENUM("pack_jsonb", "manual", name="conceptsource", create_type=False)
_kg_node_type = postgresql.ENUM(
    "pack", "subject", "chapter", "topic", "concept", name="kgnodetype", create_type=False
)
_kg_edge_type = postgresql.ENUM("contains", "part_of", name="kgedgetype", create_type=False)


def upgrade() -> None:
    _concept_source.create(op.get_bind(), checkfirst=True)
    _kg_node_type.create(op.get_bind(), checkfirst=True)
    _kg_edge_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "curriculum_concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", _concept_source, nullable=False, server_default="pack_jsonb"),
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
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["curriculum_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "topic_id", "slug", name="uq_concept_topic_slug"),
    )
    op.create_index(
        "ix_concepts_school_pack", "curriculum_concepts", ["school_id", "pack_id"]
    )
    op.create_index("ix_concepts_topic", "curriculum_concepts", ["topic_id"])

    op.create_table(
        "kg_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("edge_type", _kg_edge_type, nullable=False),
        sa.Column("from_node_type", _kg_node_type, nullable=False),
        sa.Column("from_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_node_type", _kg_node_type, nullable=False),
        sa.Column("to_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
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
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "edge_type",
            "from_node_type",
            "from_id",
            "to_node_type",
            "to_id",
            name="uq_kg_edge_endpoints",
        ),
    )
    op.create_index("ix_kg_edges_school_pack", "kg_edges", ["school_id", "pack_id"])
    op.create_index(
        "ix_kg_edges_to", "kg_edges", ["school_id", "to_node_type", "to_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_kg_edges_to", table_name="kg_edges")
    op.drop_index("ix_kg_edges_school_pack", table_name="kg_edges")
    op.drop_table("kg_edges")
    op.drop_index("ix_concepts_topic", table_name="curriculum_concepts")
    op.drop_index("ix_concepts_school_pack", table_name="curriculum_concepts")
    op.drop_table("curriculum_concepts")
    _kg_edge_type.drop(op.get_bind(), checkfirst=True)
    _kg_node_type.drop(op.get_bind(), checkfirst=True)
    _concept_source.drop(op.get_bind(), checkfirst=True)
