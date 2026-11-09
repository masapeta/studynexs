"""answer sheet pages (P2 M5, P-R4: max 12 pages)

``answer_sheet_evaluations.file_id`` stays for backward compatibility and continues to hold
page 1. Existing single-file evaluations are not rewritten; readers treat ``file_id`` as page 1
when an evaluation has no page rows.

Revision ID: r5c9e1a3d7f4
Revises: r3b8d4f6c2e7
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "r5c9e1a3d7f4"
down_revision = "r3b8d4f6c2e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "answer_sheet_pages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column("page_no", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=True),
        sa.UniqueConstraint("evaluation_id", "page_no", name="uq_answer_sheet_page_no"),
        sa.UniqueConstraint("evaluation_id", "file_id", name="uq_answer_sheet_page_file"),
        sa.ForeignKeyConstraint(
            ["school_id", "evaluation_id"],
            ["answer_sheet_evaluations.school_id", "answer_sheet_evaluations.id"],
            name="fk_answer_sheet_page_evaluation", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "file_id"], ["uploaded_files.school_id", "uploaded_files.id"],
            name="fk_answer_sheet_page_file",
        ),
        sa.CheckConstraint("page_no BETWEEN 1 AND 12", name="ck_answer_sheet_page_no"),
    )


def downgrade() -> None:
    op.drop_table("answer_sheet_pages")
