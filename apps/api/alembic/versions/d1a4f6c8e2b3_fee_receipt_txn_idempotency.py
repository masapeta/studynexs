"""partial unique index on fee_receipts(school_id, transaction_id) for payment idempotency

Revision ID: d1a4f6c8e2b3
Revises: c9f1e3a5d7b2
Create Date: 2026-06-01

Prevents duplicate receipts / over-credit from concurrent gateway callbacks sharing a
transaction_id. Partial (WHERE transaction_id IS NOT NULL) so cash payments are unaffected.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1a4f6c8e2b3"
down_revision: Union[str, None] = "c9f1e3a5d7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_receipt_txn_per_school",
        "fee_receipts",
        ["school_id", "transaction_id"],
        unique=True,
        postgresql_where=sa.text("transaction_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_receipt_txn_per_school", table_name="fee_receipts")
