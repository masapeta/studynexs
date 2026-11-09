"""exam result versions, governed releases, evaluation revisions (P2 M1 + M2)

Schema-only. No result is published or backfilled: historical baselines are created lazily at
the first release preview (decision P-R2).

Every new relationship is a composite FK that includes ``school_id`` against a
``UNIQUE (school_id, id)`` target, so the database itself rejects cross-tenant links.

M2 (``answer_sheet_evaluation_revisions``) is created here because
``exam_result_versions.evaluation_revision_id`` references it.

DOWNGRADE CAUTION: downgrading drops all result-version, release and revision history.
Only run a downgrade on a disposable database, or with explicit owner approval.

Revision ID: r1a7c3e5b9d1
Revises: p5c2e9f3b7d4
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "r1a7c3e5b9d1"
down_revision = "p5c2e9f3b7d4"
branch_labels = None
depends_on = None

_TENANT_TARGETS = (
    ("uq_exams_school_id_id", "exams"),
    ("uq_students_school_id_id", "students"),
    ("uq_users_school_id_id", "users"),
    ("uq_answer_sheet_evaluations_school_id_id", "answer_sheet_evaluations"),
    ("uq_uploaded_files_school_id_id", "uploaded_files"),
)

_STATUSES = "('not_released', 'released', 'withdrawn', 'blocked')"


def _ts() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=True),
    ]


def upgrade() -> None:
    for name, table in _TENANT_TARGETS:
        op.create_unique_constraint(name, table, ["school_id", "id"])

    op.create_table(
        "answer_sheet_evaluation_revisions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("ai_suggestions", postgresql.JSONB(), nullable=True),
        sa.Column("teacher_overrides", postgresql.JSONB(), nullable=True),
        sa.Column("input_answers", postgresql.JSONB(), nullable=True),
        sa.Column("page_file_ids", postgresql.JSONB(), nullable=True),
        sa.Column("question_marks", postgresql.JSONB(), nullable=True),
        sa.Column("marks_obtained", sa.Numeric(6, 2), nullable=True),
        sa.Column("correction_summary", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("model_info", postgresql.JSONB(), nullable=True),
        *_ts(),
        sa.UniqueConstraint("evaluation_id", "revision_no", name="uq_eval_revision_no"),
        sa.UniqueConstraint("school_id", "id", name="uq_eval_revisions_school_id_id"),
        sa.ForeignKeyConstraint(
            ["school_id", "evaluation_id"],
            ["answer_sheet_evaluations.school_id", "answer_sheet_evaluations.id"],
            name="fk_eval_revision_evaluation", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "actor_id"], ["users.school_id", "users.id"],
            name="fk_eval_revision_actor",
        ),
        sa.CheckConstraint("kind IN ('approved', 'reopened')", name="ck_eval_revision_kind"),
        sa.CheckConstraint(
            "kind <> 'reopened' OR reason IS NOT NULL", name="ck_eval_revision_reopen_reason"
        ),
    )
    op.create_index(
        "ix_eval_revisions_school_eval",
        "answer_sheet_evaluation_revisions",
        ["school_id", "evaluation_id"],
    )

    op.create_table(
        "exam_result_versions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(6, 2), nullable=False),
        sa.Column("question_marks", postgresql.JSONB(), nullable=True),
        sa.Column("grade_letter", sa.String(5), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=True),
        sa.Column("evaluation_revision_id", sa.UUID(), nullable=True),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        *_ts(),
        sa.UniqueConstraint(
            "school_id", "exam_id", "student_id", "version_no", name="uq_result_version_no"
        ),
        sa.UniqueConstraint(
            "school_id", "exam_id", "student_id", "id", name="uq_result_version_scope"
        ),
        sa.UniqueConstraint("school_id", "id", name="uq_result_versions_school_id_id"),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id"], ["exams.school_id", "exams.id"],
            name="fk_result_version_exam", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "student_id"], ["students.school_id", "students.id"],
            name="fk_result_version_student",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "evaluation_id"],
            ["answer_sheet_evaluations.school_id", "answer_sheet_evaluations.id"],
            name="fk_result_version_evaluation",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "evaluation_revision_id"],
            ["answer_sheet_evaluation_revisions.school_id",
             "answer_sheet_evaluation_revisions.id"],
            name="fk_result_version_eval_revision",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "approved_by"], ["users.school_id", "users.id"],
            name="fk_result_version_approver",
        ),
        sa.CheckConstraint(
            "source IN ('ai_evaluation', 'manual_entry', 'historical_baseline')",
            name="ck_result_version_source",
        ),
        sa.CheckConstraint("version_no >= 1", name="ck_result_version_no_positive"),
        sa.CheckConstraint("marks_obtained >= 0", name="ck_result_version_marks_nonneg"),
        sa.CheckConstraint(
            "source <> 'ai_evaluation' OR "
            "(evaluation_id IS NOT NULL AND evaluation_revision_id IS NOT NULL)",
            name="ck_result_version_ai_provenance",
        ),
        sa.CheckConstraint(
            "source = 'historical_baseline' OR approved_by IS NOT NULL",
            name="ck_result_version_approver",
        ),
    )
    op.create_index(
        "ix_result_versions_school_exam", "exam_result_versions", ["school_id", "exam_id"]
    )
    op.create_index(
        "ix_result_versions_school_student", "exam_result_versions", ["school_id", "student_id"]
    )

    op.create_table(
        "exam_result_releases",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("event_no", sa.Integer(), nullable=False),
        sa.Column("generation_no", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("actor_role", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("action_token", sa.UUID(), nullable=False),
        sa.Column("preview_fingerprint", sa.String(64), nullable=True),
        sa.Column("published_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_counts", postgresql.JSONB(), nullable=True),
        sa.Column("partial", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("prior_status", sa.String(20), nullable=False),
        sa.Column("resulting_status", sa.String(20), nullable=False),
        *_ts(),
        sa.UniqueConstraint("school_id", "exam_id", "event_no", name="uq_release_event_no"),
        sa.UniqueConstraint("school_id", "action_token", name="uq_release_action_token"),
        sa.UniqueConstraint("school_id", "exam_id", "id", name="uq_release_scope"),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id"], ["exams.school_id", "exams.id"],
            name="fk_release_exam", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "actor_id"], ["users.school_id", "users.id"],
            name="fk_release_actor",
        ),
        sa.CheckConstraint(
            "action IN ('release', 'withdraw', 'block', 'unblock')", name="ck_release_action"
        ),
        sa.CheckConstraint(f"prior_status IN {_STATUSES}", name="ck_release_prior_status"),
        sa.CheckConstraint(
            f"resulting_status IN {_STATUSES}", name="ck_release_resulting_status"
        ),
        sa.CheckConstraint(
            "(action = 'release') = (generation_no IS NOT NULL)",
            name="ck_release_generation_only_for_release",
        ),
        sa.CheckConstraint(
            "action = 'release' OR reason IS NOT NULL", name="ck_release_reason_required"
        ),
    )
    op.create_index(
        "uq_release_generation_no",
        "exam_result_releases",
        ["school_id", "exam_id", "generation_no"],
        unique=True,
        postgresql_where=sa.text("generation_no IS NOT NULL"),
    )

    op.create_table(
        "exam_result_release_items",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("release_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("result_version_id", sa.UUID(), nullable=False),
        *_ts(),
        sa.UniqueConstraint("release_id", "student_id", name="uq_release_item_student"),
        sa.UniqueConstraint(
            "release_id", "student_id", "result_version_id", name="uq_release_item_manifest"
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id", "release_id"],
            ["exam_result_releases.school_id", "exam_result_releases.exam_id",
             "exam_result_releases.id"],
            name="fk_release_item_release", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id", "student_id", "result_version_id"],
            ["exam_result_versions.school_id", "exam_result_versions.exam_id",
             "exam_result_versions.student_id", "exam_result_versions.id"],
            name="fk_release_item_version", ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_release_items_school_exam", "exam_result_release_items", ["school_id", "exam_id"]
    )

    op.create_table(
        "exam_result_published",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("result_version_id", sa.UUID(), nullable=False),
        sa.Column("release_id", sa.UUID(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        *_ts(),
        sa.UniqueConstraint(
            "school_id", "exam_id", "student_id", name="uq_published_exam_student"
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id", "student_id", "result_version_id"],
            ["exam_result_versions.school_id", "exam_result_versions.exam_id",
             "exam_result_versions.student_id", "exam_result_versions.id"],
            name="fk_published_version", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id", "release_id"],
            ["exam_result_releases.school_id", "exam_result_releases.exam_id",
             "exam_result_releases.id"],
            name="fk_published_release", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["release_id", "student_id", "result_version_id"],
            ["exam_result_release_items.release_id", "exam_result_release_items.student_id",
             "exam_result_release_items.result_version_id"],
            name="fk_published_manifest_item", ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_published_school_student", "exam_result_published", ["school_id", "student_id"]
    )

    op.create_table(
        "exam_result_notifications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("release_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("result_version_id", sa.UUID(), nullable=False),
        sa.Column("recipient_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "notification_id", sa.UUID(),
            sa.ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True,
        ),
        *_ts(),
        sa.UniqueConstraint(
            "release_id", "student_id", "recipient_user_id", name="uq_result_notification"
        ),
        sa.ForeignKeyConstraint(
            ["release_id", "student_id", "result_version_id"],
            ["exam_result_release_items.release_id", "exam_result_release_items.student_id",
             "exam_result_release_items.result_version_id"],
            name="fk_result_notification_manifest", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "recipient_user_id"], ["users.school_id", "users.id"],
            name="fk_result_notification_recipient",
        ),
    )

    op.create_table(
        "exam_release_state",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_released"),
        sa.Column("current_generation_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_event_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status_before_block", sa.String(20), nullable=True),
        sa.Column("blocked_by", sa.UUID(), nullable=True),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        *_ts(),
        sa.UniqueConstraint("school_id", "exam_id", name="uq_release_state_exam"),
        sa.ForeignKeyConstraint(
            ["school_id", "exam_id"], ["exams.school_id", "exams.id"],
            name="fk_release_state_exam", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id", "blocked_by"], ["users.school_id", "users.id"],
            name="fk_release_state_blocked_by",
        ),
        sa.CheckConstraint(f"status IN {_STATUSES}", name="ck_release_state_status"),
        sa.CheckConstraint(
            "(status = 'blocked') = (status_before_block IS NOT NULL)",
            name="ck_release_state_block_memory",
        ),
        sa.CheckConstraint(
            "status_before_block IS NULL OR status_before_block <> 'blocked'",
            name="ck_release_state_no_nested_block",
        ),
    )


def downgrade() -> None:
    op.drop_table("exam_release_state")
    op.drop_table("exam_result_notifications")
    op.drop_index("ix_published_school_student", table_name="exam_result_published")
    op.drop_table("exam_result_published")
    op.drop_index("ix_release_items_school_exam", table_name="exam_result_release_items")
    op.drop_table("exam_result_release_items")
    op.drop_index("uq_release_generation_no", table_name="exam_result_releases")
    op.drop_table("exam_result_releases")
    op.drop_index("ix_result_versions_school_student", table_name="exam_result_versions")
    op.drop_index("ix_result_versions_school_exam", table_name="exam_result_versions")
    op.drop_table("exam_result_versions")
    op.drop_index(
        "ix_eval_revisions_school_eval", table_name="answer_sheet_evaluation_revisions"
    )
    op.drop_table("answer_sheet_evaluation_revisions")
    for name, table in reversed(_TENANT_TARGETS):
        op.drop_constraint(name, table, type_="unique")
