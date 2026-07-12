"""Document Intelligence: ingestion audit table for pack-scoped document indexing.

Revision ID: x4e5f6a7b8c9
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "x4e5f6a7b8c9"
down_revision = "w3d4e5f6a7b8"
branch_labels = None
depends_on = None

_doc_type = postgresql.ENUM(
    "worksheet", "circular", "notes", "other", name="documenttype", create_type=False
)
_ingest_status = postgresql.ENUM(
    "pending", "completed", "failed", name="ingeststatus", create_type=False
)


def upgrade() -> None:
    _doc_type.create(op.get_bind(), checkfirst=True)
    _ingest_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "document_ingestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", _doc_type, nullable=False),
        sa.Column("status", _ingest_status, nullable=False, server_default="pending"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("chunks_indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(300), nullable=False),
        sa.Column("ingested_by", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["ingested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["pack_id"], ["curriculum_packs.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_doc_ingest_school_pack", "document_ingestions", ["school_id", "pack_id"]
    )
    op.create_index(
        "ix_doc_ingest_pack_file", "document_ingestions", ["pack_id", "file_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_doc_ingest_pack_file", table_name="document_ingestions")
    op.drop_index("ix_doc_ingest_school_pack", table_name="document_ingestions")
    op.drop_table("document_ingestions")
    _ingest_status.drop(op.get_bind(), checkfirst=True)
    _doc_type.drop(op.get_bind(), checkfirst=True)
