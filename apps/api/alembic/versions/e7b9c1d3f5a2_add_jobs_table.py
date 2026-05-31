"""add jobs table (async job queue)

Revision ID: e7b9c1d3f5a2
Revises: c3a1f0d2e4b6
Create Date: 2026-05-31

Backing store for the Arq-based async job queue: status + params + result/error
for background tasks (AI generation, grading, reports) so the UI can poll progress.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e7b9c1d3f5a2"
down_revision: Union[str, None] = "c3a1f0d2e4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("school_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("QUEUED", "RUNNING", "DONE", "FAILED", name="jobstatus"),
            nullable=False,
        ),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_school_status", "jobs", ["school_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_jobs_school_status", table_name="jobs")
    op.drop_table("jobs")
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
