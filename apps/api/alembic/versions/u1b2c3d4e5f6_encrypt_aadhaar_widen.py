"""Encrypt Aadhaar at rest: widen columns so the Fernet ciphertext fits.

Aadhaar numbers move from plaintext String(12) to application-encrypted tokens
(app/core/encryption.EncryptedString). This only widens the columns — it does NOT transform
data, so the rollout is backward-compatible: existing plaintext rows keep reading (the type
falls back to plaintext for non-tokens) and are encrypted on their next write. Re-encrypting
historical rows is a separate, optional backfill.

Revision ID: u1b2c3d4e5f6
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "u1b2c3d4e5f6"
down_revision = "t0a1b2c3d4e5"
branch_labels = None
depends_on = None

_TABLES = ("admission_candidates", "staff_profiles")


def upgrade() -> None:
    for table in _TABLES:
        op.alter_column(
            table,
            "aadhaar_number",
            existing_type=sa.String(length=12),
            type_=sa.String(length=512),
            existing_nullable=True,
        )


def downgrade() -> None:
    # Reverse of the widen. Safe on plaintext/empty data; if encrypted (>12 char) tokens exist,
    # decrypt or clear them before downgrading (inherent to at-rest encryption).
    for table in _TABLES:
        op.alter_column(
            table,
            "aadhaar_number",
            existing_type=sa.String(length=512),
            type_=sa.String(length=12),
            existing_nullable=True,
        )
