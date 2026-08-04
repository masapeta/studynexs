"""Defense-in-depth tenancy on join tables

student_parent_map, notice_read_receipts, and student_transport were scoped
only through JOINs to their tenant-owned parents — the same gap the
notifications table had (war-room f31). Constitution §22 requires every
tenant-owned row to carry its own school_id. Add the column, backfill from
the unambiguous parent, then enforce NOT NULL — all in one transactional
migration because the backfill source is total (every existing row has a
parent row to inherit from).

Revision ID: a6c8e0b2d4f6
Revises: f4b6d8a0c2e4
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "a6c8e0b2d4f6"
down_revision = "f4b6d8a0c2e4"
branch_labels = None
depends_on = None

_TABLES = (
    # (table, backfill source join)
    (
        "student_parent_map",
        """
        UPDATE student_parent_map t
        SET school_id = s.school_id
        FROM students s
        WHERE s.id = t.student_id AND t.school_id IS NULL
        """,
    ),
    (
        "notice_read_receipts",
        """
        UPDATE notice_read_receipts t
        SET school_id = n.school_id
        FROM notices n
        WHERE n.id = t.notice_id AND t.school_id IS NULL
        """,
    ),
    (
        "student_transport",
        """
        UPDATE student_transport t
        SET school_id = s.school_id
        FROM students s
        WHERE s.id = t.student_id AND t.school_id IS NULL
        """,
    ),
)


def upgrade() -> None:
    for table, backfill in _TABLES:
        op.add_column(
            table,
            sa.Column(
                "school_id",
                sa.UUID(),
                sa.ForeignKey("schools.id"),
                nullable=True,
            ),
        )
        op.execute(backfill)
        op.alter_column(table, "school_id", nullable=False)
        op.create_index(f"ix_{table}_school", table, ["school_id"])


def downgrade() -> None:
    for table, _ in reversed(_TABLES):
        op.drop_index(f"ix_{table}_school", table_name=table)
        op.drop_column(table, "school_id")
