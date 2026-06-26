"""Admission candidate identity document numbers.

Revision ID: q7d3e9f1g5i
Revises: p6c2d8f0g4h
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "q7d3e9f1g5i"
down_revision = "p6c2d8f0g4h"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("admission_candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("admission_candidates")}
    if "aadhaar_number" not in existing:
        op.add_column(
            "admission_candidates",
            sa.Column("aadhaar_number", sa.String(length=12), nullable=True),
        )
    if "birth_certificate_number" not in existing:
        op.add_column(
            "admission_candidates",
            sa.Column("birth_certificate_number", sa.String(length=40), nullable=True),
        )
    if "apaar_number" not in existing:
        op.add_column(
            "admission_candidates",
            sa.Column("apaar_number", sa.String(length=30), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("admission_candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("admission_candidates")}
    if "apaar_number" in existing:
        op.drop_column("admission_candidates", "apaar_number")
    if "birth_certificate_number" in existing:
        op.drop_column("admission_candidates", "birth_certificate_number")
    if "aadhaar_number" in existing:
        op.drop_column("admission_candidates", "aadhaar_number")
