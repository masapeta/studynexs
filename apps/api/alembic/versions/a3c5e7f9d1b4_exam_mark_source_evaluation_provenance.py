"""exam_marks.source_evaluation_id — provenance FK to approved evaluations

Links each authoritative mark row back to the answer-sheet evaluation it was
finalized from, closing the evidence-ledger gap where approved marks lost
their HITL trail (AI suggestions, teacher overrides, approver).

Additive + reversible. Backfills existing AI-graded marks where exactly one
approved evaluation matches (exam_id, student_id, school_id); ambiguous or
manual marks stay NULL by design.

Revision ID: a3c5e7f9d1b4
Revises: f7e8d9c0b1a2
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "a3c5e7f9d1b4"
down_revision = "f7e8d9c0b1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exam_marks",
        sa.Column(
            "source_evaluation_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "answer_sheet_evaluations.id",
                name="fk_exam_marks_source_evaluation",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_exam_marks_source_evaluation_id",
        "exam_marks",
        ["source_evaluation_id"],
    )
    # Backfill: AI-graded marks with exactly one approved evaluation for the
    # same (exam, student, school). Tenant-safe — join carries school_id.
    op.execute(
        """
        UPDATE exam_marks em
        SET source_evaluation_id = ase.id
        FROM answer_sheet_evaluations ase
        WHERE em.ai_graded = TRUE
          AND em.source_evaluation_id IS NULL
          AND ase.exam_id = em.exam_id
          AND ase.student_id = em.student_id
          AND ase.school_id = em.school_id
          AND ase.status = 'approved'
          AND NOT EXISTS (
              SELECT 1 FROM answer_sheet_evaluations dup
              WHERE dup.exam_id = em.exam_id
                AND dup.student_id = em.student_id
                AND dup.school_id = em.school_id
                AND dup.status = 'approved'
                AND dup.id <> ase.id
          )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_exam_marks_source_evaluation_id", table_name="exam_marks")
    op.drop_constraint("fk_exam_marks_source_evaluation", "exam_marks", type_="foreignkey")
    op.drop_column("exam_marks", "source_evaluation_id")
