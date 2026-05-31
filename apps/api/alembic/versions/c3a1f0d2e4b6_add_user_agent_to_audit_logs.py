"""add user_agent to audit_logs

Revision ID: c3a1f0d2e4b6
Revises: b2c3d4e5f6a7
Create Date: 2026-05-31

Fixes the audit middleware writing a non-existent column: AuditMiddleware
constructs AuditLog(user_agent=...) but the table had no such column, so every
mutating request's audit insert raised (and was silently swallowed). Adding the
column makes audit logging actually persist in production.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c3a1f0d2e4b6"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("user_agent", sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "user_agent")
