"""Drop parents.relationship_type — contract phase of DM-2c

Expand-then-contract, final step. b6d8f0a2c4e6 added the per-link
student_parent_map.relationship_type and backfilled it; all writers have set
the link-level value since. This migration:

1. backfills any straggler NULL links from the parent row (safety net);
2. makes the link-level column NOT NULL (it is now the only source);
3. drops the parent-level column.

The `relationship` enum type stays — student_parent_map still uses it.

Revision ID: e2a4c6d8f0b2
Revises: c7e9a1b3d5f7
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "e2a4c6d8f0b2"
down_revision = "c7e9a1b3d5f7"
branch_labels = None
depends_on = None

_relationship_enum = sa.Enum(
    "FATHER", "MOTHER", "GUARDIAN", name="relationship", create_type=False
)


def upgrade() -> None:
    # Safety net: any link still NULL inherits its parent's value before the
    # source column disappears.
    op.execute(
        """
        UPDATE student_parent_map spm
        SET relationship_type = p.relationship_type
        FROM parents p
        WHERE spm.parent_id = p.id
          AND spm.relationship_type IS NULL
        """
    )
    op.alter_column(
        "student_parent_map",
        "relationship_type",
        existing_type=_relationship_enum,
        nullable=False,
    )
    op.drop_column("parents", "relationship_type")


def downgrade() -> None:
    # Re-create the parent-level column and derive it from the links: the
    # primary link's relationship wins, else any link, else GUARDIAN (a parent
    # row with no links carries no relationship information to restore).
    op.add_column(
        "parents",
        sa.Column("relationship_type", _relationship_enum, nullable=True),
    )
    op.execute(
        """
        UPDATE parents p
        SET relationship_type = sub.relationship_type
        FROM (
            SELECT DISTINCT ON (parent_id) parent_id, relationship_type
            FROM student_parent_map
            ORDER BY parent_id, is_primary DESC, created_at ASC
        ) sub
        WHERE sub.parent_id = p.id
        """
    )
    op.execute(
        "UPDATE parents SET relationship_type = 'GUARDIAN' WHERE relationship_type IS NULL"
    )
    op.alter_column(
        "parents",
        "relationship_type",
        existing_type=_relationship_enum,
        nullable=False,
    )
    op.alter_column(
        "student_parent_map",
        "relationship_type",
        existing_type=_relationship_enum,
        nullable=True,
    )
