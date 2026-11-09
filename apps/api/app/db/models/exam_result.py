"""Exam result versions and governed release (P2 Stage 2, plan Rev 2 §3).

Model:
- ``ExamResultVersion`` — append-only snapshot of one student's approved result for one exam.
  Created by EVERY mark write (``ExamService.enter_marks``), never edited.
- ``ExamResultRelease`` — append-only event log per exam (release / withdraw / block / unblock).
  Only ``release`` events carry a ``generation_no``.
- ``ExamResultReleaseItem`` — manifest: the exact version each release published per student.
- ``ExamResultPublished`` — current learner-visible pointer per (exam, student). It can only
  reference a manifest item (composite FK), so nothing unpublished can ever be pointed at.
- ``ExamReleaseState`` — per-exam state row, row-locked during transitions.

Tenant consistency is enforced by the database: every relationship is a composite FK that
includes ``school_id`` against a ``UNIQUE (school_id, id)`` target, so a row can never join to
another tenant's exam, student, user, evaluation or release.

Learner visibility = published pointer exists AND ``ExamReleaseState.status == 'released'``.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel

RESULT_SOURCE_AI_EVALUATION = "ai_evaluation"
RESULT_SOURCE_MANUAL_ENTRY = "manual_entry"
RESULT_SOURCE_HISTORICAL_BASELINE = "historical_baseline"
RESULT_SOURCES = (
    RESULT_SOURCE_AI_EVALUATION,
    RESULT_SOURCE_MANUAL_ENTRY,
    RESULT_SOURCE_HISTORICAL_BASELINE,
)

RELEASE_ACTION_RELEASE = "release"
RELEASE_ACTION_WITHDRAW = "withdraw"
RELEASE_ACTION_BLOCK = "block"
RELEASE_ACTION_UNBLOCK = "unblock"
RELEASE_ACTIONS = (
    RELEASE_ACTION_RELEASE,
    RELEASE_ACTION_WITHDRAW,
    RELEASE_ACTION_BLOCK,
    RELEASE_ACTION_UNBLOCK,
)

RELEASE_STATUS_NOT_RELEASED = "not_released"
RELEASE_STATUS_RELEASED = "released"
RELEASE_STATUS_WITHDRAWN = "withdrawn"
RELEASE_STATUS_BLOCKED = "blocked"
RELEASE_STATUSES = (
    RELEASE_STATUS_NOT_RELEASED,
    RELEASE_STATUS_RELEASED,
    RELEASE_STATUS_WITHDRAWN,
    RELEASE_STATUS_BLOCKED,
)


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class ExamResultVersion(BaseModel):
    __tablename__ = "exam_result_versions"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    question_marks: Mapped[dict | None] = mapped_column(JSONB)
    grade_letter: Mapped[str | None] = mapped_column(String(5))
    # Teacher-approved text only (remarks / approved correction summary) — never raw AI text.
    feedback: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    evaluation_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    # NULL only for historical baselines whose original approver is unknown.
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "school_id", "exam_id", "student_id", "version_no", name="uq_result_version_no"
        ),
        # Composite target so manifests/pointers must match tenant + exam + student.
        UniqueConstraint(
            "school_id", "exam_id", "student_id", "id", name="uq_result_version_scope"
        ),
        UniqueConstraint("school_id", "id", name="uq_result_versions_school_id_id"),
        ForeignKeyConstraint(
            ["school_id", "exam_id"],
            ["exams.school_id", "exams.id"],
            name="fk_result_version_exam",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "student_id"],
            ["students.school_id", "students.id"],
            name="fk_result_version_student",
        ),
        ForeignKeyConstraint(
            ["school_id", "evaluation_id"],
            ["answer_sheet_evaluations.school_id", "answer_sheet_evaluations.id"],
            name="fk_result_version_evaluation",
        ),
        ForeignKeyConstraint(
            ["school_id", "evaluation_revision_id"],
            [
                "answer_sheet_evaluation_revisions.school_id",
                "answer_sheet_evaluation_revisions.id",
            ],
            name="fk_result_version_eval_revision",
        ),
        ForeignKeyConstraint(
            ["school_id", "approved_by"],
            ["users.school_id", "users.id"],
            name="fk_result_version_approver",
        ),
        CheckConstraint(_in("source", RESULT_SOURCES), name="ck_result_version_source"),
        CheckConstraint("version_no >= 1", name="ck_result_version_no_positive"),
        CheckConstraint("marks_obtained >= 0", name="ck_result_version_marks_nonneg"),
        CheckConstraint(
            "source <> 'ai_evaluation' OR "
            "(evaluation_id IS NOT NULL AND evaluation_revision_id IS NOT NULL)",
            name="ck_result_version_ai_provenance",
        ),
        CheckConstraint(
            "source = 'historical_baseline' OR approved_by IS NOT NULL",
            name="ck_result_version_approver",
        ),
        Index("ix_result_versions_school_exam", "school_id", "exam_id"),
        Index("ix_result_versions_school_student", "school_id", "student_id"),
    )


class ExamResultRelease(BaseModel):
    __tablename__ = "exam_result_releases"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    # Monotonic per exam across every action (audit ordering).
    event_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # Only release events have a generation number (1, 2, 3, ...).
    generation_no: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    action_token: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    preview_fingerprint: Mapped[str | None] = mapped_column(String(64))
    published_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_counts: Mapped[dict | None] = mapped_column(JSONB)
    partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # State before this event — block/unblock restore it exactly.
    prior_status: Mapped[str] = mapped_column(String(20), nullable=False)
    resulting_status: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "exam_id", "event_no", name="uq_release_event_no"),
        UniqueConstraint("school_id", "action_token", name="uq_release_action_token"),
        UniqueConstraint("school_id", "exam_id", "id", name="uq_release_scope"),
        Index(
            "uq_release_generation_no",
            "school_id",
            "exam_id",
            "generation_no",
            unique=True,
            postgresql_where=text("generation_no IS NOT NULL"),
        ),
        ForeignKeyConstraint(
            ["school_id", "exam_id"],
            ["exams.school_id", "exams.id"],
            name="fk_release_exam",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "actor_id"],
            ["users.school_id", "users.id"],
            name="fk_release_actor",
        ),
        CheckConstraint(_in("action", RELEASE_ACTIONS), name="ck_release_action"),
        CheckConstraint(_in("prior_status", RELEASE_STATUSES), name="ck_release_prior_status"),
        CheckConstraint(
            _in("resulting_status", RELEASE_STATUSES), name="ck_release_resulting_status"
        ),
        CheckConstraint(
            "(action = 'release') = (generation_no IS NOT NULL)",
            name="ck_release_generation_only_for_release",
        ),
        CheckConstraint(
            "action = 'release' OR reason IS NOT NULL", name="ck_release_reason_required"
        ),
    )


class ExamResultReleaseItem(BaseModel):
    __tablename__ = "exam_result_release_items"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    release_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    result_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("release_id", "student_id", name="uq_release_item_student"),
        UniqueConstraint(
            "release_id", "student_id", "result_version_id", name="uq_release_item_manifest"
        ),
        ForeignKeyConstraint(
            ["school_id", "exam_id", "release_id"],
            ["exam_result_releases.school_id", "exam_result_releases.exam_id",
             "exam_result_releases.id"],
            name="fk_release_item_release",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "exam_id", "student_id", "result_version_id"],
            ["exam_result_versions.school_id", "exam_result_versions.exam_id",
             "exam_result_versions.student_id", "exam_result_versions.id"],
            name="fk_release_item_version",
            ondelete="CASCADE",
        ),
        Index("ix_release_items_school_exam", "school_id", "exam_id"),
    )


class ExamResultPublished(BaseModel):
    __tablename__ = "exam_result_published"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    result_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    release_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("school_id", "exam_id", "student_id", name="uq_published_exam_student"),
        ForeignKeyConstraint(
            ["school_id", "exam_id", "student_id", "result_version_id"],
            ["exam_result_versions.school_id", "exam_result_versions.exam_id",
             "exam_result_versions.student_id", "exam_result_versions.id"],
            name="fk_published_version",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "exam_id", "release_id"],
            ["exam_result_releases.school_id", "exam_result_releases.exam_id",
             "exam_result_releases.id"],
            name="fk_published_release",
            ondelete="CASCADE",
        ),
        # A pointer can only reference a version the named release actually published.
        ForeignKeyConstraint(
            ["release_id", "student_id", "result_version_id"],
            ["exam_result_release_items.release_id", "exam_result_release_items.student_id",
             "exam_result_release_items.result_version_id"],
            name="fk_published_manifest_item",
            ondelete="CASCADE",
        ),
        Index("ix_published_school_student", "school_id", "student_id"),
    )


class ExamResultNotification(BaseModel):
    """Dedupe ledger for release notifications (P-R7, safeguard 7).

    One row per (release generation, student, recipient). The unique key makes a second
    notification for the same generation/student/recipient impossible, and the composite FK to
    the manifest ties every notification to the exact published version it announced.
    """

    __tablename__ = "exam_result_notifications"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    release_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    result_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    notification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="SET NULL")
    )

    __table_args__ = (
        UniqueConstraint(
            "release_id", "student_id", "recipient_user_id", name="uq_result_notification"
        ),
        ForeignKeyConstraint(
            ["release_id", "student_id", "result_version_id"],
            ["exam_result_release_items.release_id", "exam_result_release_items.student_id",
             "exam_result_release_items.result_version_id"],
            name="fk_result_notification_manifest",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "recipient_user_id"],
            ["users.school_id", "users.id"],
            name="fk_result_notification_recipient",
        ),
    )


class ExamReleaseState(BaseModel):
    __tablename__ = "exam_release_state"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RELEASE_STATUS_NOT_RELEASED
    )
    current_generation_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_event_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # While blocked: the status to restore on unblock.
    status_before_block: Mapped[str | None] = mapped_column(String(20))
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    blocked_reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("school_id", "exam_id", name="uq_release_state_exam"),
        ForeignKeyConstraint(
            ["school_id", "exam_id"],
            ["exams.school_id", "exams.id"],
            name="fk_release_state_exam",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["school_id", "blocked_by"],
            ["users.school_id", "users.id"],
            name="fk_release_state_blocked_by",
        ),
        CheckConstraint(_in("status", RELEASE_STATUSES), name="ck_release_state_status"),
        CheckConstraint(
            "(status = 'blocked') = (status_before_block IS NOT NULL)",
            name="ck_release_state_block_memory",
        ),
        CheckConstraint(
            "status_before_block IS NULL OR status_before_block <> 'blocked'",
            name="ck_release_state_no_nested_block",
        ),
    )
