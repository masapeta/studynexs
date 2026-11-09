"""Learner-facing report cards (P2 Stage 2, plan Rev 2 E14).

A card reaches a parent/student only when it is teacher-approved, carries an exam manifest, and
EVERY manifest exam currently has a learner-visible published result for that student
(``visible_versions_query``). Subject figures are recomputed from those published versions, never
from the staff snapshot or ``exam_marks``. The approved remark is shown only while the published
figures still equal the snapshot it was written against; otherwise it is withheld.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.exam_result import ExamResultVersion
from app.db.models.report_card import ReportCard, ReportStatus
from app.db.models.student import Student
from app.modules.ai.services.report_card_service import _grade
from app.modules.examinations.services.release_service import visible_versions_query


class LearnerReportSubject(BaseModel):
    subject: str
    marks_obtained: float
    total_marks: float


class LearnerReportCard(BaseModel):
    id: uuid.UUID
    title: str
    student_name: str
    class_name: str
    subjects: list[LearnerReportSubject]
    not_assessed: list[str] = []
    total_obtained: float
    total_max: float
    percentage: float
    overall_grade: str
    attendance_percentage: float | None = None
    remark: str | None = None
    remark_withheld: bool = False


def _money(v: float) -> Decimal:
    return Decimal(str(round(v, 2)))


async def _published_by_exam(
    db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID, exam_ids: set[uuid.UUID]
) -> dict[uuid.UUID, tuple[ExamResultVersion, object]]:
    if not exam_ids:
        return {}
    rows = (
        await db.execute(
            visible_versions_query(school_id).where(
                ExamResultVersion.student_id == student_id,
                ExamResultVersion.exam_id.in_(exam_ids),
            )
        )
    ).all()
    return {version.exam_id: (version, exam) for version, _pub, exam in rows}


def _manifest(card: ReportCard) -> set[uuid.UUID] | None:
    if not card.exam_ids:
        return None
    try:
        return {uuid.UUID(str(x)) for x in card.exam_ids}
    except ValueError:
        return None


async def _build(
    db: AsyncSession, school_id: uuid.UUID, card: ReportCard
) -> LearnerReportCard | None:
    manifest = _manifest(card)
    if manifest is None:
        return None
    published = await _published_by_exam(db, school_id, card.student_id, manifest)
    if set(published) != manifest:
        return None

    subject_names = dict(
        (
            await db.execute(
                select(Subject.id, Subject.name).where(
                    Subject.school_id == school_id,
                    Subject.id.in_({exam.subject_id for _v, exam in published.values()}),
                )
            )
        ).all()
    )
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for version, exam in published.values():
        name = subject_names.get(exam.subject_id, "Subject")
        sums[name][0] += float(version.marks_obtained)
        sums[name][1] += float(exam.total_marks)
    subjects = [
        LearnerReportSubject(subject=name, marks_obtained=o, total_marks=t)
        for name, (o, t) in sorted(sums.items())
    ]
    total_obtained = sum(s.marks_obtained for s in subjects)
    total_max = sum(s.total_marks for s in subjects)
    if total_max <= 0 or total_obtained < 0 or total_obtained > total_max:
        return None
    percentage = round(total_obtained / total_max * 100, 2)

    snapshot = sorted(
        (str(s.get("subject")), _money(float(s.get("marks_obtained") or 0)),
         _money(float(s.get("total_marks") or 0)))
        for s in (card.subjects or [])
    )
    live = sorted((s.subject, _money(s.marks_obtained), _money(s.total_marks)) for s in subjects)
    matches_snapshot = snapshot == live

    return LearnerReportCard(
        id=card.id,
        title=card.title,
        student_name=card.student_name,
        class_name=card.class_name,
        subjects=subjects,
        not_assessed=list(card.not_assessed or []),
        total_obtained=total_obtained,
        total_max=total_max,
        percentage=percentage,
        overall_grade=_grade(percentage),
        attendance_percentage=(
            float(card.attendance_percentage) if card.attendance_percentage is not None else None
        ),
        remark=card.ai_remark if matches_snapshot else None,
        remark_withheld=bool(card.ai_remark) and not matches_snapshot,
    )


async def list_report_cards(
    db: AsyncSession, *, school_id: uuid.UUID, student: Student
) -> list[LearnerReportCard]:
    cards = (
        await db.execute(
            select(ReportCard)
            .where(
                ReportCard.school_id == school_id,
                ReportCard.student_id == student.id,
                ReportCard.status == ReportStatus.APPROVED,
            )
            .order_by(ReportCard.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    out: list[LearnerReportCard] = []
    for card in cards:
        built = await _build(db, school_id, card)
        if built is not None:
            out.append(built)
    return out


async def report_card_detail(
    db: AsyncSession, *, school_id: uuid.UUID, student: Student, report_id: uuid.UUID
) -> LearnerReportCard | None:
    card = (
        await db.execute(
            select(ReportCard).where(
                ReportCard.id == report_id,
                ReportCard.school_id == school_id,
                ReportCard.student_id == student.id,
                ReportCard.status == ReportStatus.APPROVED,
            )
        )
    ).scalar_one_or_none()
    if card is None:
        return None
    return await _build(db, school_id, card)
