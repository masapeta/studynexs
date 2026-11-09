"""Learner-facing exam results (plan Rev 2 §5.4, E13).

The ONLY read path for student/parent result data. Everything comes from
``visible_versions_query`` (published pointer AND exam status == released), so withdrawn,
blocked, unpublished or unreleased results can never appear here. Exams of the student's class
that have no visible result are listed as ``pending`` with no figures.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.exam_result import ExamResultVersion
from app.db.models.examination import Exam
from app.db.models.student import Student
from app.modules.examinations.schemas.release import LearnerResultDetail, LearnerResultSummary
from app.modules.examinations.services.release_service import visible_versions_query


def _pct(obtained: float, total: float) -> float | None:
    return round(obtained / total * 100, 1) if total else None


async def list_results(
    db: AsyncSession, *, school_id: uuid.UUID, student: Student
) -> list[LearnerResultSummary]:
    visible = {
        version.exam_id: (version, pub)
        for version, pub, _exam in (
            await db.execute(
                visible_versions_query(school_id).where(
                    ExamResultVersion.student_id == student.id
                )
            )
        ).all()
    }
    # Current class exams (pending or released) plus any released result from an earlier class.
    in_scope = Exam.class_id == student.class_id
    if visible:
        in_scope = in_scope | Exam.id.in_(list(visible))
    exams = (
        await db.execute(
            select(Exam, Subject.name)
            .join(Subject, (Subject.id == Exam.subject_id) & (Subject.school_id == school_id))
            .where(Exam.school_id == school_id, in_scope)
            .order_by(Exam.date.desc().nullslast(), Exam.created_at.desc())
            .limit(200)
        )
    ).all()
    out: list[LearnerResultSummary] = []
    for exam, subject_name in exams:
        hit = visible.get(exam.id)
        if hit is None:
            out.append(
                LearnerResultSummary(
                    exam_id=exam.id,
                    exam_title=exam.title,
                    subject_name=subject_name,
                    exam_date=exam.date,
                    status="pending",
                )
            )
            continue
        version, pub = hit
        obtained, total = float(version.marks_obtained), float(exam.total_marks)
        out.append(
            LearnerResultSummary(
                exam_id=exam.id,
                exam_title=exam.title,
                subject_name=subject_name,
                exam_date=exam.date,
                status="released",
                marks_obtained=obtained,
                total_marks=total,
                percentage=_pct(obtained, total),
                grade_letter=version.grade_letter,
                published_at=pub.published_at,
            )
        )
    return out


async def result_detail(
    db: AsyncSession, *, school_id: uuid.UUID, student: Student, exam_id: uuid.UUID
) -> LearnerResultDetail | None:
    """Question-wise marks + teacher-approved feedback of the PUBLISHED version only."""
    row = (
        await db.execute(
            visible_versions_query(school_id).where(
                ExamResultVersion.student_id == student.id,
                ExamResultVersion.exam_id == exam_id,
            )
        )
    ).first()
    exam_row = (
        await db.execute(
            select(Exam, Subject.name)
            .join(Subject, (Subject.id == Exam.subject_id) & (Subject.school_id == school_id))
            .where(Exam.id == exam_id, Exam.school_id == school_id)
        )
    ).first()
    if exam_row is None:
        return None
    exam, subject_name = exam_row
    if row is None:
        if exam.class_id != student.class_id:
            return None
        return LearnerResultDetail(
            exam_id=exam.id,
            exam_title=exam.title,
            subject_name=subject_name,
            exam_date=exam.date,
            status="pending",
        )
    version, pub, _exam = row
    obtained, total = float(version.marks_obtained), float(exam.total_marks)
    max_marks = {
        str(q["no"]): float(q["max_marks"])
        for q in (exam.question_schema or [])
        if isinstance(q, dict) and q.get("no") is not None
    }
    return LearnerResultDetail(
        exam_id=exam.id,
        exam_title=exam.title,
        subject_name=subject_name,
        exam_date=exam.date,
        status="released",
        marks_obtained=obtained,
        total_marks=total,
        percentage=_pct(obtained, total),
        grade_letter=version.grade_letter,
        published_at=pub.published_at,
        question_marks=version.question_marks,
        question_max_marks=max_marks or None,
        feedback=version.feedback,
    )
