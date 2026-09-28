"""parent intervention drafts + batches

Revision ID: n4b1d8e2a6c3
Revises: m3a9c2e7f1b0
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "n4b1d8e2a6c3"
down_revision = "m3a9c2e7f1b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parent_intervention_batches",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=True),
    )
    op.create_index(
        "ix_parent_intervention_batch_school", "parent_intervention_batches", ["school_id"]
    )

    op.create_table(
        "parent_intervention_drafts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "batch_id", sa.UUID(),
            sa.ForeignKey("parent_intervention_batches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("student_id", sa.UUID(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("parent_user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(length=60), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column(
            "notification_id", sa.UUID(), sa.ForeignKey("notifications.id"), nullable=True
        ),
        sa.Column("approved_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=True),
        sa.UniqueConstraint(
            "batch_id", "student_id", "parent_user_id",
            name="uq_intervention_batch_student_parent",
        ),
    )
    op.create_index(
        "ix_intervention_draft_school_status", "parent_intervention_drafts",
        ["school_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_intervention_draft_school_status", table_name="parent_intervention_drafts")
    op.drop_table("parent_intervention_drafts")
    op.drop_index(
        "ix_parent_intervention_batch_school", table_name="parent_intervention_batches"
    )
    op.drop_table("parent_intervention_batches")
