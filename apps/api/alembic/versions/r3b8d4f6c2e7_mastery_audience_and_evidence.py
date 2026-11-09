"""mastery audience separation, provenance evidence, KG audience, pending-gap dedupe (P2 M3)

- ``student_topic_mastery.audience`` ('staff' | 'learner', default 'staff'); the unique key
  ``uq_student_topic_mastery`` now includes audience so both ledgers coexist.
- ``mastery_flags.audience`` (default 'staff').
- ``kg_edges.audience`` ('shared' | 'staff' | 'learner', default 'shared'); existing
  STRUGGLES_WITH edges were computed from all approved marks, so they are labelled 'staff'.
  ``uq_kg_edge_endpoints`` now includes audience so staff and learner evidence edges never
  overwrite each other.
- ``mastery_evidence`` provenance table.
- Partial unique index: one pending concept-card gap per (school, concept).

Existing ledger rows keep their values and are labelled 'staff'. Learner rows are created by
the next recompute; nothing becomes learner-visible from this migration.

DOWNGRADE CAUTION: removes learner-audience rows (they cannot be represented without the
audience column) and drops provenance evidence. Disposable databases or owner approval only.

Revision ID: r3b8d4f6c2e7
Revises: r1a7c3e5b9d1
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "r3b8d4f6c2e7"
down_revision = "r1a7c3e5b9d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_topic_mastery",
        sa.Column("audience", sa.String(10), nullable=False, server_default="staff"),
    )
    op.create_check_constraint(
        "ck_stm_audience", "student_topic_mastery", "audience IN ('staff', 'learner')"
    )
    op.drop_constraint("uq_student_topic_mastery", "student_topic_mastery", type_="unique")
    op.create_unique_constraint(
        "uq_student_topic_mastery",
        "student_topic_mastery",
        ["student_id", "subject_id", "academic_year_id", "topic", "audience"],
    )

    op.add_column(
        "mastery_flags",
        sa.Column("audience", sa.String(10), nullable=False, server_default="staff"),
    )
    op.create_check_constraint(
        "ck_mastery_flags_audience", "mastery_flags", "audience IN ('staff', 'learner')"
    )

    op.add_column(
        "kg_edges",
        sa.Column("audience", sa.String(10), nullable=False, server_default="shared"),
    )
    # ::text: on a fresh chain the enum value is added earlier in this same transaction, and
    # Postgres forbids using a not-yet-committed enum literal.
    op.execute("UPDATE kg_edges SET audience = 'staff' WHERE edge_type::text = 'struggles_with'")
    op.create_check_constraint(
        "ck_kg_edges_audience", "kg_edges", "audience IN ('shared', 'staff', 'learner')"
    )
    op.drop_constraint("uq_kg_edge_endpoints", "kg_edges", type_="unique")
    op.create_unique_constraint(
        "uq_kg_edge_endpoints",
        "kg_edges",
        ["school_id", "edge_type", "from_node_type", "from_id", "to_node_type", "to_id",
         "audience"],
    )

    op.create_table(
        "mastery_evidence",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("subject_id", sa.UUID(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("audience", sa.String(10), nullable=False),
        sa.Column("evidence_source", sa.String(30), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=True),
        sa.Column("result_version_id", sa.UUID(), nullable=True),
        sa.Column(
            "exam_mark_id", sa.UUID(),
            sa.ForeignKey("exam_marks.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("assessed_on", sa.Date(), nullable=False),
        sa.Column("recompute_run_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=True),
        sa.ForeignKeyConstraint(
            ["school_id", "student_id"], ["students.school_id", "students.id"],
            name="fk_mastery_evidence_student",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id"], ["exams.school_id", "exams.id"],
            name="fk_mastery_evidence_exam", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "result_version_id"],
            ["exam_result_versions.school_id", "exam_result_versions.id"],
            name="fk_mastery_evidence_version", ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "audience IN ('staff', 'learner')", name="ck_mastery_evidence_audience"
        ),
        sa.CheckConstraint(
            "evidence_source IN ('exam_result')", name="ck_mastery_evidence_source"
        ),
        sa.CheckConstraint(
            "audience <> 'learner' OR result_version_id IS NOT NULL",
            name="ck_mastery_evidence_learner_version",
        ),
        sa.CheckConstraint(
            "audience <> 'staff' OR exam_mark_id IS NOT NULL",
            name="ck_mastery_evidence_staff_mark",
        ),
    )
    op.create_index(
        "ix_mastery_evidence_scope",
        "mastery_evidence",
        ["school_id", "class_id", "subject_id", "audience"],
    )
    op.create_index(
        "ix_mastery_evidence_student", "mastery_evidence", ["school_id", "student_id", "audience"]
    )

    op.create_index(
        "uq_content_review_pending_gap",
        "content_review_items",
        ["school_id", "concept_id"],
        unique=True,
        postgresql_where=sa.text("item_type = 'concept_card_gap' AND status = 'pending'"),
    )

    # Safeguard 3: misconceptions carry the exact originating evaluation revision.
    op.add_column(
        "misconception_entries",
        sa.Column(
            "source_evaluation_revision_id", sa.UUID(),
            sa.ForeignKey(
                "answer_sheet_evaluation_revisions.id",
                name="fk_misconception_source_revision",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_misconception_source_revision", "misconception_entries", type_="foreignkey"
    )
    op.drop_column("misconception_entries", "source_evaluation_revision_id")
    op.drop_index("uq_content_review_pending_gap", table_name="content_review_items")
    op.drop_index("ix_mastery_evidence_student", table_name="mastery_evidence")
    op.drop_index("ix_mastery_evidence_scope", table_name="mastery_evidence")
    op.drop_table("mastery_evidence")

    op.execute("DELETE FROM kg_edges WHERE audience = 'learner'")
    op.drop_constraint("uq_kg_edge_endpoints", "kg_edges", type_="unique")
    op.create_unique_constraint(
        "uq_kg_edge_endpoints",
        "kg_edges",
        ["school_id", "edge_type", "from_node_type", "from_id", "to_node_type", "to_id"],
    )
    op.drop_constraint("ck_kg_edges_audience", "kg_edges", type_="check")
    op.drop_column("kg_edges", "audience")

    op.execute("DELETE FROM mastery_flags WHERE audience = 'learner'")
    op.drop_constraint("ck_mastery_flags_audience", "mastery_flags", type_="check")
    op.drop_column("mastery_flags", "audience")

    op.execute("DELETE FROM student_topic_mastery WHERE audience = 'learner'")
    op.drop_constraint("uq_student_topic_mastery", "student_topic_mastery", type_="unique")
    op.create_unique_constraint(
        "uq_student_topic_mastery",
        "student_topic_mastery",
        ["student_id", "subject_id", "academic_year_id", "topic"],
    )
    op.drop_constraint("ck_stm_audience", "student_topic_mastery", type_="check")
    op.drop_column("student_topic_mastery", "audience")
