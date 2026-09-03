"""Staff HR onboarding profiles.

Revision ID: r8e4f0g2h6j
Revises: q7d3e9f1g5i
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "r8e4f0g2h6j"
down_revision = "q7d3e9f1g5i"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=10), nullable=True),
        sa.Column("aadhaar_number", sa.String(length=12), nullable=True),
        sa.Column("address_line", sa.String(length=300), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("qualification", sa.Text(), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("employee_id", sa.String(length=50), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("previous_experience", sa.Text(), nullable=True),
        sa.Column("aadhaar_document_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("experience_document_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["aadhaar_document_file_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["experience_document_file_id"], ["uploaded_files.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_staff_profiles_user"),
    )
    op.create_index("ix_staff_profiles_school", "staff_profiles", ["school_id"])


def downgrade() -> None:
    op.drop_index("ix_staff_profiles_school", table_name="staff_profiles")
    op.drop_table("staff_profiles")
