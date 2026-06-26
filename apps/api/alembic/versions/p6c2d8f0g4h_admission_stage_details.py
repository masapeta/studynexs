"""Admission stage-specific details (application, offer, enrollment).

Revision ID: p6c2d8f0g4h
Revises: o5b1c7e9f3g
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "p6c2d8f0g4h"
down_revision = "o5b1c7e9f3g"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("admission_candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("admission_candidates")}
    if "stage_details" not in existing:
        op.add_column(
            "admission_candidates",
            sa.Column(
                "stage_details",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("admission_candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("admission_candidates")}
    if "stage_details" in existing:
        op.drop_column("admission_candidates", "stage_details")
