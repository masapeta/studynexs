"""Admission enquiry — extended candidate details.

Revision ID: o5b1c7e9f3g
Revises: n4a0b6d8e2f
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "o5b1c7e9f3g"
down_revision = "n4a0b6d8e2f"
branch_labels = None
depends_on = None

_NEW_COLS = (
    ("date_of_birth", sa.Date()),
    ("gender", sa.String(length=20)),
    ("parent_name", sa.String(length=120)),
    ("parent_relation", sa.String(length=20)),
    ("parent_occupation", sa.String(length=120)),
    ("parent_mobile", sa.String(length=20)),
    ("parent_email", sa.String(length=120)),
    ("address_line", sa.String(length=300)),
    ("city", sa.String(length=80)),
    ("previous_school_name", sa.String(length=200)),
    ("previous_grade", sa.String(length=40)),
    ("enquiry_source", sa.String(length=40)),
)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("admission_candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("admission_candidates")}
    for name, col_type in _NEW_COLS:
        if name not in existing:
            op.add_column("admission_candidates", sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("admission_candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("admission_candidates")}
    for name, _ in reversed(_NEW_COLS):
        if name in existing:
            op.drop_column("admission_candidates", name)
