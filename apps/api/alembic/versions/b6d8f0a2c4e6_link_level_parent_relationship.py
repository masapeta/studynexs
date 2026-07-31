"""student_parent_map.relationship_type — per-link parent relationship (expand phase)

A user can be "father" to one student and "guardian" to another; the
relationship belongs on the student↔parent link, not the parent row.

Expand-then-contract step 1: add nullable enum column on the map, backfill
from parents.relationship_type. Parent.relationship_type stays (dual-write)
until the contract phase in a later release.

Revision ID: b6d8f0a2c4e6
Revises: a3c5e7f9d1b4
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "b6d8f0a2c4e6"
down_revision = "a3c5e7f9d1b4"
branch_labels = None
depends_on = None

# Reuse the existing enum type created by the parents table.
_relationship_enum = sa.Enum(
    "FATHER", "MOTHER", "GUARDIAN", name="relationship", create_type=False
)


def upgrade() -> None:
    op.add_column(
        "student_parent_map",
        sa.Column("relationship_type", _relationship_enum, nullable=True),
    )
    # Backfill each link from its parent row's current relationship.
    op.execute(
        """
        UPDATE student_parent_map spm
        SET relationship_type = p.relationship_type
        FROM parents p
        WHERE spm.parent_id = p.id
          AND spm.relationship_type IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("student_parent_map", "relationship_type")
