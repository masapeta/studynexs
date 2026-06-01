"""race-safety: fee idempotency_key + one-active-year-per-school

Revision ID: e2b5a7c9f1d4
Revises: d1a4f6c8e2b3
Create Date: 2026-06-01

- fee_receipts.idempotency_key (+ partial unique index) — client idempotency for ALL
  payments incl. cash (which has no transaction_id).
- partial unique index on academic_years(school_id) WHERE is_active — DB-enforce
  "one active year per school" (closes the silent concurrent double-activation race).
  NOTE: build fails if a school already has >1 active year; backfill first if so.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e2b5a7c9f1d4"
down_revision: Union[str, None] = "d1a4f6c8e2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fee_receipts", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
    op.create_index(
        "uq_receipt_idem_per_school", "fee_receipts", ["school_id", "idempotency_key"],
        unique=True, postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "uq_one_active_year_per_school", "academic_years", ["school_id"],
        unique=True, postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index("uq_one_active_year_per_school", table_name="academic_years")
    op.drop_index("uq_receipt_idem_per_school", table_name="fee_receipts")
    op.drop_column("fee_receipts", "idempotency_key")
