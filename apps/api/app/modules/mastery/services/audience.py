"""Audience selection + learner-exposure gates for derived learning data (plan Rev 2 §4.2–§4.3).

Learner roles (student, parent) may only ever read the ``learner`` audience, which is built
exclusively from released result versions. Staff roles read the ``staff`` audience (all
approved marks). Unknown roles are treated as learners (fail-secure).
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exam_result import (
    RELEASE_STATUS_RELEASED,
    ExamReleaseState,
    ExamResultPublished,
    ExamResultVersion,
)
from app.db.models.examination import ExamMark
from app.db.models.mastery import AUDIENCE_LEARNER, AUDIENCE_STAFF, MasteryFlag
from app.db.models.misconception import MisconceptionEntry

STAFF_ROLES = frozenset({"teacher", "class_incharge", "admin", "super_admin", "operations"})


def audience_for_role(role: str | None) -> str:
    return AUDIENCE_STAFF if role in STAFF_ROLES else AUDIENCE_LEARNER


def _released_pointer_join(school_id: uuid.UUID):
    """Published pointers whose exam is currently released (the learner-visibility rule)."""
    return (
        select(ExamResultPublished, ExamResultVersion)
        .join(
            ExamResultVersion,
            (ExamResultVersion.id == ExamResultPublished.result_version_id)
            & (ExamResultVersion.school_id == school_id),
        )
        .join(
            ExamReleaseState,
            (ExamReleaseState.exam_id == ExamResultPublished.exam_id)
            & (ExamReleaseState.school_id == school_id),
        )
        .where(
            ExamResultPublished.school_id == school_id,
            ExamReleaseState.status == RELEASE_STATUS_RELEASED,
        )
    )


async def flag_evidence_is_released(
    db: AsyncSession, school_id: uuid.UUID, flag: MasteryFlag
) -> bool:
    """True only if every exam behind the flag is released at the student's CURRENT mark.

    The flag's frozen evidence lists the contributing exams. Each must have a released,
    published version for this student, and that version must equal the staff mark the flag
    was computed from (no unreleased later changes). Otherwise the note would disclose
    unreleased results to a parent.
    """
    exam_ids: set[uuid.UUID] = set()
    for point in (flag.evidence or {}).get("history") or []:
        try:
            exam_ids.add(uuid.UUID(str(point.get("exam_id"))))
        except (TypeError, ValueError, AttributeError):
            return False
    if not exam_ids:
        return False
    published = {
        pub.exam_id: version
        for pub, version in (
            await db.execute(
                _released_pointer_join(school_id).where(
                    ExamResultPublished.student_id == flag.student_id,
                    ExamResultPublished.exam_id.in_(exam_ids),
                )
            )
        ).all()
    }
    if set(published) != exam_ids:
        return False
    marks = {
        m.exam_id: m
        for m in (
            await db.execute(
                select(ExamMark).where(
                    ExamMark.school_id == school_id,
                    ExamMark.student_id == flag.student_id,
                    ExamMark.exam_id.in_(exam_ids),
                )
            )
        ).scalars().all()
    }
    for exam_id, version in published.items():
        mark = marks.get(exam_id)
        if mark is None or float(mark.marks_obtained) != float(version.marks_obtained):
            return False
        if (mark.question_marks or None) != (version.question_marks or None):
            return False
    return True


async def published_misconceptions_for_student(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
    limit: int = 5,
) -> list[MisconceptionEntry]:
    """Safeguard 3: learner-visible misconceptions.

    An entry is exposed only when the student's currently released, published result version
    carries EXACTLY the evaluation revision that produced the entry. No "later version"
    comparisons: if the student was re-evaluated and the new result is not yet released (or
    the entry came from a different revision), the entry stays staff-only. Legacy entries
    without a revision id are never learner-visible.
    """
    released_revisions = (
        _released_pointer_join(school_id)
        .where(
            ExamResultPublished.student_id == student_id,
            ExamResultVersion.evaluation_revision_id.is_not(None),
        )
        .with_only_columns(ExamResultVersion.evaluation_revision_id)
    )
    return list(
        (
            await db.execute(
                select(MisconceptionEntry)
                .where(
                    MisconceptionEntry.school_id == school_id,
                    MisconceptionEntry.student_id == student_id,
                    MisconceptionEntry.source_evaluation_revision_id.in_(released_revisions),
                )
                .order_by(MisconceptionEntry.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
    )
