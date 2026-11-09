"""Append-only exam result versions (plan Rev 2 §3.1, safeguard 5).

Every mark write in the platform goes through ``ExamService.enter_marks`` (manual gradebook
entry, AI-evaluation approval, re-approval after reopen, bulk entry, governed actions), and
``enter_marks`` calls :func:`append_versions` in the same transaction. There is no other code
path that writes ``exam_marks`` (verified by grep; ``tests/test_exam_result_versions.py``
guards it).

Concurrency: callers hold the ``exam_marks`` row lock (``SELECT ... FOR UPDATE``) for the
(exam, student) pair before computing the next ``version_no``; the unique constraint
``uq_result_version_no`` is the backstop.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditLog
from app.db.models.exam_result import (
    RESULT_SOURCE_HISTORICAL_BASELINE,
    RESULT_SOURCE_MANUAL_ENTRY,
    ExamResultVersion,
)
from app.db.models.examination import ExamMark


@dataclass(frozen=True)
class VersionProvenance:
    """Who/what produced the marks being written."""

    source: str = RESULT_SOURCE_MANUAL_ENTRY
    actor_id: uuid.UUID | None = None
    evaluation_id: uuid.UUID | None = None
    evaluation_revision_id: uuid.UUID | None = None
    # Teacher-approved feedback text override (AI approvals pass the approved summary).
    feedback: str | None = None


def _same_content(version: ExamResultVersion, mark: ExamMark, feedback: str | None) -> bool:
    return (
        Decimal(str(version.marks_obtained)) == Decimal(str(mark.marks_obtained))
        and (version.question_marks or None) == (mark.question_marks or None)
        and (version.grade_letter or None) == (mark.grade_letter or None)
        and (version.feedback or None) == (feedback or None)
    )


async def latest_versions(
    db: AsyncSession, school_id: uuid.UUID, exam_id: uuid.UUID
) -> dict[uuid.UUID, ExamResultVersion]:
    """Latest version per student for one exam (one query)."""
    ranked = (
        select(
            ExamResultVersion.id,
            func.row_number()
            .over(
                partition_by=ExamResultVersion.student_id,
                order_by=ExamResultVersion.version_no.desc(),
            )
            .label("rn"),
        )
        .where(ExamResultVersion.school_id == school_id, ExamResultVersion.exam_id == exam_id)
        .subquery()
    )
    rows = (
        await db.execute(
            select(ExamResultVersion)
            .join(ranked, ranked.c.id == ExamResultVersion.id)
            .where(ranked.c.rn == 1)
        )
    ).scalars().all()
    return {v.student_id: v for v in rows}


async def append_versions(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    exam_id: uuid.UUID,
    student_ids: list[uuid.UUID],
    provenance: VersionProvenance,
) -> list[ExamResultVersion]:
    """Append a version for each student whose stored mark differs from their latest version.

    Called after the ``exam_marks`` upsert, inside the same transaction. A re-save with
    identical content (a retry, or a no-op edit) creates no version. An AI-evaluation approval
    always creates a version, because it carries new provenance (a new revision).
    """
    if not student_ids:
        return []
    marks = (
        await db.execute(
            select(ExamMark)
            .where(
                ExamMark.school_id == school_id,
                ExamMark.exam_id == exam_id,
                ExamMark.student_id.in_(student_ids),
            )
            .order_by(ExamMark.student_id)
            .with_for_update()
            # The marks were just written by a Core upsert; an ORM object already in the
            # identity map would otherwise be returned with stale values.
            .execution_options(populate_existing=True)
        )
    ).scalars().all()
    if not marks:
        return []
    latest = {
        sid: v
        for sid, v in (await latest_versions(db, school_id, exam_id)).items()
        if sid in set(student_ids)
    }

    now = datetime.now(timezone.utc)
    created: list[ExamResultVersion] = []
    for mark in marks:
        feedback = provenance.feedback if provenance.feedback is not None else mark.remarks
        prev = latest.get(mark.student_id)
        if (
            prev is not None
            and provenance.evaluation_revision_id is None
            and _same_content(prev, mark, feedback)
        ):
            continue
        version = ExamResultVersion(
            school_id=school_id,
            exam_id=exam_id,
            student_id=mark.student_id,
            version_no=(prev.version_no + 1) if prev else 1,
            marks_obtained=mark.marks_obtained,
            question_marks=mark.question_marks,
            grade_letter=mark.grade_letter,
            feedback=feedback,
            source=provenance.source,
            evaluation_id=provenance.evaluation_id,
            evaluation_revision_id=provenance.evaluation_revision_id,
            approved_by=provenance.actor_id,
            approved_at=now,
        )
        db.add(version)
        created.append(version)
    if not created:
        return []
    await db.flush()
    for version in created:
        db.add(
            AuditLog(
                school_id=school_id,
                user_id=provenance.actor_id,
                action="result.version_created",
                resource_type="exam_result",
                resource_id=str(exam_id),
                details={
                    "student_id": str(version.student_id),
                    "version_no": version.version_no,
                    "source": version.source,
                    "evaluation_id": str(version.evaluation_id) if version.evaluation_id else None,
                    "evaluation_revision_id": (
                        str(version.evaluation_revision_id)
                        if version.evaluation_revision_id
                        else None
                    ),
                },
            )
        )
    await db.flush()
    return created


async def ensure_historical_baselines(
    db: AsyncSession, *, school_id: uuid.UUID, exam_id: uuid.UUID
) -> int:
    """P-R2: lazily anchor legacy marks (entered before versioning) as unpublished baselines.

    Idempotent and tenant-scoped. Runs inside the caller's transaction while it holds the
    exam's release-state row lock, so two previews cannot create duplicate baselines; the unique
    ``(school, exam, student, version_no)`` constraint is the backstop. Nothing is published.
    """
    versioned = select(ExamResultVersion.student_id).where(
        ExamResultVersion.school_id == school_id, ExamResultVersion.exam_id == exam_id
    )
    legacy = (
        await db.execute(
            select(ExamMark)
            .where(
                ExamMark.school_id == school_id,
                ExamMark.exam_id == exam_id,
                ExamMark.student_id.not_in(versioned),
            )
            .with_for_update()
        )
    ).scalars().all()
    if not legacy:
        return 0
    for mark in legacy:
        db.add(
            ExamResultVersion(
                school_id=school_id,
                exam_id=exam_id,
                student_id=mark.student_id,
                version_no=1,
                marks_obtained=mark.marks_obtained,
                question_marks=mark.question_marks,
                grade_letter=mark.grade_letter,
                feedback=mark.remarks,
                source=RESULT_SOURCE_HISTORICAL_BASELINE,
                evaluation_id=None,
                evaluation_revision_id=None,
                approved_by=None,
                approved_at=mark.updated_at or mark.created_at,
            )
        )
    await db.flush()
    db.add(
        AuditLog(
            school_id=school_id,
            user_id=None,
            action="result.historical_baselines_created",
            resource_type="exam_result",
            resource_id=str(exam_id),
            details={"count": len(legacy), "published": False},
        )
    )
    await db.flush()
    return len(legacy)
