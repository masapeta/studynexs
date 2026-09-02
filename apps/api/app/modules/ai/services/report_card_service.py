"""Report-card consolidation — the school's stated #1 pain.

Gathers a student's marks across every exam (grouped per subject), computes totals,
percentage, grade and attendance, then drafts a short constructive remark via the LLM
gateway. The remark is a DRAFT: the class teacher edits/approves before the card is issued
(human-in-the-loop). Pure consolidation of data the school already entered — the AI only
writes the prose remark, grounded strictly in the numbers it is given.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.academic import Class, Subject
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.report_card import ReportCard, ReportStatus
from app.db.models.student import Student
from app.modules.ai.gateway import LLMMessage, generate_llm, record_usage
from app.modules.ai.gateway.output_guard import sanitize_llm_plain_text
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits

logger = structlog.get_logger()
settings = get_settings()

# Percentage -> letter grade (CBSE/SSC 9-point style).
_GRADE_BANDS = [
    (91, "A1"), (81, "A2"), (71, "B1"), (61, "B2"),
    (51, "C1"), (41, "C2"), (33, "D1"), (0, "E"),
]


def _grade(pct: float) -> str:
    for lo, g in _GRADE_BANDS:
        if pct >= lo:
            return g
    return "E"


async def _consolidate_marks(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID,
    academic_year_id: uuid.UUID | None = None, exam_type: ExamType | None = None,
) -> list[dict]:
    """Sum marks for one academic year and optional exam type."""
    query = (
        select(
            Subject.name,
            func.sum(ExamMark.marks_obtained),
            func.sum(Exam.total_marks),
        )
        .join(Exam, ExamMark.exam_id == Exam.id)
        .join(Subject, Exam.subject_id == Subject.id)
        .join(Class, Exam.class_id == Class.id)
        .where(ExamMark.student_id == student_id, ExamMark.school_id == school_id)
    )
    if academic_year_id is not None:
        query = query.where(Class.academic_year_id == academic_year_id)
    if exam_type is not None:
        query = query.where(Exam.exam_type == exam_type)
    rows = (await db.execute(query.group_by(Subject.name).order_by(Subject.name))).all()
    return [
        {
            "subject": name,
            "marks_obtained": float(obtained or 0),
            "total_marks": float(total or 0),
        }
        for name, obtained, total in rows
    ]


async def _not_assessed_subjects(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID, class_id: uuid.UUID,
    academic_year_id: uuid.UUID | None = None, exam_type: ExamType | None = None,
) -> list[str]:
    """Subjects the student's class was examined in, but for which this student has no marks.

    Consolidation only sees subjects the student actually has marks in, so a skipped/absent
    subject would otherwise vanish from the card. This surfaces those gaps by name.
    """
    assessed = (
        select(Exam.subject_id)
        .join(ExamMark, (ExamMark.exam_id == Exam.id) & (ExamMark.student_id == student_id))
        .join(Class, Exam.class_id == Class.id)
        .where(Exam.class_id == class_id, Exam.school_id == school_id)
    )
    if academic_year_id is not None:
        assessed = assessed.where(Class.academic_year_id == academic_year_id)
    if exam_type is not None:
        assessed = assessed.where(Exam.exam_type == exam_type)
    rows = (
        await db.execute(
            select(Subject.name)
            .join(Exam, Exam.subject_id == Subject.id)
            .join(Class, Exam.class_id == Class.id)
            .where(
                Exam.class_id == class_id,
                Exam.school_id == school_id,
                Subject.id.not_in(assessed.scalar_subquery()),
            )
            .distinct()
            .order_by(Subject.name)
        )
    ).scalars().all()
    return list(rows)


async def _attendance_percentage(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID,
    academic_year_id: uuid.UUID,
) -> float | None:
    """Weighted attendance %: present/late = 1 day, half-day = 0.5, absent = 0."""
    rows = (
        await db.execute(
            select(Attendance.status, func.count())
            .join(Class, Attendance.class_id == Class.id)
            .where(Attendance.student_id == student_id, Attendance.school_id == school_id)
            .where(Class.academic_year_id == academic_year_id)
            .group_by(Attendance.status)
        )
    ).all()
    total = sum(c for _, c in rows)
    if total == 0:
        return None
    weight = {
        AttendanceStatus.PRESENT: 1.0,
        AttendanceStatus.LATE: 1.0,
        AttendanceStatus.HALF_DAY: 0.5,
        AttendanceStatus.ABSENT: 0.0,
    }
    credited = sum(weight.get(s, 0.0) * c for s, c in rows)
    return round(credited / total * 100, 1)


def _build_remark_messages(
    *, student_name, class_name, subjects, percentage, grade, attendance_pct,
    not_assessed=None,
) -> list[LLMMessage]:
    lines = "\n".join(
        f"- {s['subject']}: {s['marks_obtained']:g}/{s['total_marks']:g} "
        f"({(s['marks_obtained'] / s['total_marks'] * 100) if s['total_marks'] else 0:.0f}%)"
        for s in subjects
    )
    att = f"{attendance_pct:g}%" if attendance_pct is not None else "not recorded"
    not_assessed_line = (
        f"Not assessed this term (do not comment on these): {', '.join(not_assessed)}.\n"
        if not_assessed
        else ""
    )
    system = (
        "You are an experienced Indian school class teacher writing the remark on a "
        "student's term report card, read by the parent. Write 2-3 warm, specific, "
        "constructive sentences. Name the student's strongest and weakest subject by name, "
        "acknowledge effort, and give one concrete, encouraging suggestion for improvement. "
        "Base everything STRICTLY on the data given — invent no facts, no marks, no events. "
        "Do not restate the numbers. Plain text only, no headings or bullet points."
    )
    user = (
        f"Student: {student_name} (Class {class_name})\n"
        f"Subject performance:\n{lines}\n"
        f"{not_assessed_line}"
        f"Overall: {percentage:.0f}% (Grade {grade}). Attendance: {att}.\n\n"
        "Write the report-card remark."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


async def generate_report_for_student(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    created_by: uuid.UUID,
    student_id: uuid.UUID,
    title: str | None = None,
    academic_year_id: uuid.UUID | None = None,
    exam_type: ExamType | None = None,
    role: str = "teacher",
    credits_charged: int | None = None,
) -> ReportCard:
    """Consolidate one student's results + attendance and draft a remark. Returns a DRAFT."""
    student = (
        await db.execute(
            select(Student).where(Student.id == student_id, Student.school_id == school_id)
        )
    ).scalar_one_or_none()
    if student is None:
        raise ValueError("Student not found")

    if academic_year_id is None:
        academic_year_id = (
            await db.execute(
                select(Class.academic_year_id).where(
                    Class.id == student.class_id,
                    Class.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
    if academic_year_id is None:
        raise ValueError("Student is not assigned to an academic year")

    subjects = await _consolidate_marks(
        db,
        school_id=school_id,
        student_id=student_id,
        academic_year_id=academic_year_id,
        exam_type=exam_type,
    )
    if not subjects:
        raise ValueError("No exam marks recorded for this student yet — enter marks first.")

    total_obtained = sum(s["marks_obtained"] for s in subjects)
    total_max = sum(s["total_marks"] for s in subjects)
    if total_max <= 0 or total_obtained < 0 or total_obtained > total_max:
        raise ValueError("Report card totals are outside the valid range")
    percentage = round(total_obtained / total_max * 100, 2)
    grade = _grade(percentage)
    attendance_pct = await _attendance_percentage(
        db,
        school_id=school_id,
        student_id=student_id,
        academic_year_id=academic_year_id,
    )
    not_assessed = await _not_assessed_subjects(
        db,
        school_id=school_id,
        student_id=student_id,
        class_id=student.class_id,
        academic_year_id=academic_year_id,
        exam_type=exam_type,
    )

    student_name = student.user.full_name if student.user else "Student"
    cls = student.class_
    class_name = f"{cls.grade} - {cls.section}" if cls else ""

    messages = _build_remark_messages(
        student_name=student_name, class_name=class_name, subjects=subjects,
        percentage=percentage, grade=grade, attendance_pct=attendance_pct,
        not_assessed=not_assessed,
    )
    cost = credits_charged if credits_charged is not None else credits_for_purpose("report_card")
    reserved = None
    if cost > 0:
        reserved = await reserve_ai_credits(
            db,
            school_id,
            user_id=created_by,
            role=role,
            purpose_tag="report_card",
            feature="report_card",
            credits=cost,
            ref_type="report_card",
        )

    try:
        result = await generate_llm(
            messages, max_tokens=300, temperature=0.5,
            feature="report_card", caller="generate_report_for_student",
        )
    except Exception as exc:
        if settings.is_development and not (settings.AI_FALLBACK_PROVIDER or "").strip():
            logger.warning("report_card_llm_failed_using_stub", error=str(exc))
            from app.modules.ai.gateway.stub import StubProvider

            result = await StubProvider().generate(
                messages, model="dev-stub", max_tokens=300, temperature=0.5
            )
        else:
            raise
    remark = sanitize_llm_plain_text(result.text, max_length=4000) or None

    report = ReportCard(
        school_id=school_id,
        student_id=student_id,
        class_id=student.class_id,
        created_by=created_by,
        title=title or "Term Report Card",
        student_name=student_name,
        class_name=class_name,
        subjects=subjects,
        not_assessed=not_assessed,
        total_obtained=Decimal(str(round(total_obtained, 2))),
        total_max=Decimal(str(round(total_max, 2))),
        percentage=Decimal(str(percentage)),
        overall_grade=grade,
        attendance_percentage=(
            Decimal(str(attendance_pct)) if attendance_pct is not None else None
        ),
        ai_remark=remark,
        status=ReportStatus.DRAFT,
        ai_model=f"{result.provider}:{result.model}",
    )
    db.add(report)
    await db.flush()

    await record_usage(
        db,
        feature="report_card",
        result=result,
        reserved_row=reserved,
        ref_type="report_card",
        ref_id=report.id,
    )
    logger.info(
        "report_card_generated",
        report_id=str(report.id),
        student_id=str(student_id),
        percentage=percentage,
        grade=grade,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
    )
    return report
