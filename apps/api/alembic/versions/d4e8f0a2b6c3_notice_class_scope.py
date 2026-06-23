"""Add class_id to notices for class-scoped announcements.

Revision ID: d4e8f0a2b6c3
Revises: a9d4e6f8c0b2
Create Date: 2026-06-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d4e8f0a2b6c3"
down_revision = "a9d4e6f8c0b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notices",
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_notices_class_id",
        "notices",
        "classes",
        ["class_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_notices_school_class", "notices", ["school_id", "class_id"])


def downgrade() -> None:
    op.drop_index("ix_notices_school_class", table_name="notices")
    op.drop_constraint("fk_notices_class_id", "notices", type_="foreignkey")
    op.drop_column("notices", "class_id")
