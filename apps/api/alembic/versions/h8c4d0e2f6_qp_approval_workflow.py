"""Question paper approval workflow — reject, submit, extended statuses.

Revision ID: h8c4d0e2f6
Revises: g7b3c9d1e2f4
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "h8c4d0e2f6"
down_revision = "g7b3c9d1e2f4"
branch_labels = None
depends_on = None

_NEW_STATUSES = (
    "edited",
    "pending_approval",
    "rejected",
    "published",
    "archived",
)


def upgrade() -> None:
    # Original migration used uppercase labels; SQLAlchemy model uses lowercase values.
    op.execute("ALTER TYPE paperstatus RENAME VALUE 'DRAFT' TO 'draft'")
    op.execute("ALTER TYPE paperstatus RENAME VALUE 'APPROVED' TO 'approved'")
    for val in _NEW_STATUSES:
        op.execute(
            f"DO $$ BEGIN ALTER TYPE paperstatus ADD VALUE '{val}'; "
            "EXCEPTION WHEN duplicate_object THEN null; END $$;"
        )
    op.add_column("question_papers", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column(
        "question_papers",
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "question_papers",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "question_papers",
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_question_papers_rejected_by",
        "question_papers",
        "users",
        ["rejected_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_question_papers_rejected_by", "question_papers", type_="foreignkey")
    op.drop_column("question_papers", "submitted_at")
    op.drop_column("question_papers", "rejected_at")
    op.drop_column("question_papers", "rejected_by")
    op.drop_column("question_papers", "rejection_reason")
    # PostgreSQL cannot remove enum values without recreating the type — leave extended values.
