"""Question bank polish — approval_status enum to string, JSONB server default.

Revision ID: j0d6e2f4a8b
Revises: i9c5d1e3f7a

No-op when i9c5d1e3f7a already created approval_status as varchar (fresh installs).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "j0d6e2f4a8b"
down_revision = "i9c5d1e3f7a"
branch_labels = None
depends_on = None


def _column_udt(table: str, column: str) -> str | None:
    row = op.get_bind().execute(
        sa.text(
            "SELECT udt_name FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row[0] if row else None


def upgrade() -> None:
    udt = _column_udt("question_bank_items", "approval_status")
    if udt == "bankapprovalstatus":
        op.execute(
            "ALTER TABLE question_bank_items "
            "ALTER COLUMN approval_status TYPE varchar(20) "
            "USING approval_status::text"
        )
        op.execute("DROP TYPE bankapprovalstatus")
    op.execute(
        "ALTER TABLE question_bank_items "
        "ALTER COLUMN approval_status SET DEFAULT 'approved'"
    )
    op.execute(
        "ALTER TABLE question_bank_items "
        "ALTER COLUMN used_in_paper_ids SET DEFAULT '[]'::jsonb"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE question_bank_items "
        "ALTER COLUMN used_in_paper_ids DROP DEFAULT"
    )
    op.execute(
        "ALTER TABLE question_bank_items "
        "ALTER COLUMN approval_status DROP DEFAULT"
    )
    udt = _column_udt("question_bank_items", "approval_status")
    if udt == "varchar":
        op.execute(
            "DO $$ BEGIN CREATE TYPE bankapprovalstatus AS ENUM ('approved'); "
            "EXCEPTION WHEN duplicate_object THEN null; END $$;"
        )
        op.execute(
            "ALTER TABLE question_bank_items "
            "ALTER COLUMN approval_status TYPE bankapprovalstatus "
            "USING approval_status::bankapprovalstatus"
        )
