"""Admin ops hub — admissions, payroll, expenses, transport capacity.

Revision ID: n4a0b6d8e2f
Revises: m3f9a5c7b1d
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "n4a0b6d8e2f"
down_revision = "m3f9a5c7b1d"
branch_labels = None
depends_on = None

_admission_stage = postgresql.ENUM(
    "enquiry", "applied", "interview", "offer", "enrolled",
    name="admissionstage",
    create_type=False,
)
_payroll_status = postgresql.ENUM("pending", "paid", name="payrollstatus", create_type=False)


def _ensure_enums() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE admissionstage AS ENUM (
                'enquiry', 'applied', 'interview', 'offer', 'enrolled'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE payrollstatus AS ENUM ('pending', 'paid');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def upgrade() -> None:
    _ensure_enums()

    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("transport_routes")}
    if "capacity" not in cols:
        op.add_column(
            "transport_routes",
            sa.Column("capacity", sa.Integer(), nullable=False, server_default="30"),
        )

    if not insp.has_table("admission_candidates"):
        op.create_table(
            "admission_candidates",
            sa.Column("school_id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("grade_applied", sa.String(length=40), nullable=False),
            sa.Column("stage", _admission_stage, nullable=False, server_default="enquiry"),
            sa.Column("enquiry_date", sa.Date(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.UUID(), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not insp.has_table("staff_payroll_entries"):
        op.create_table(
            "staff_payroll_entries",
            sa.Column("school_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("period_month", sa.Date(), nullable=False),
            sa.Column("gross_amount", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("status", _payroll_status, nullable=False, server_default="pending"),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("school_id", "user_id", "period_month", name="uq_payroll_user_month"),
        )

    if not insp.has_table("school_expenses"):
        op.create_table(
            "school_expenses",
            sa.Column("school_id", sa.UUID(), nullable=False),
            sa.Column("vendor", sa.String(length=200), nullable=False),
            sa.Column("category", sa.String(length=60), nullable=False),
            sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("expense_date", sa.Date(), nullable=False),
            sa.Column("receipt_file_id", sa.UUID(), nullable=True),
            sa.Column("created_by", sa.UUID(), nullable=False),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["receipt_file_id"], ["uploaded_files.id"]),
            sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    op.drop_table("school_expenses")
    op.drop_table("staff_payroll_entries")
    op.drop_table("admission_candidates")
    op.drop_column("transport_routes", "capacity")
    _payroll_status.drop(op.get_bind(), checkfirst=True)
    _admission_stage.drop(op.get_bind(), checkfirst=True)
