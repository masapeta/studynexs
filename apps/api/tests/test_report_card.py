"""Report-card consolidation: subjects the class was examined in but the student has no
marks for must surface as 'not assessed', not silently vanish. Service-level (no LLM call):
exercises the pure DB helper directly.
"""
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.report_card import ReportCard, ReportStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.services.report_card_service import (
    _consolidate_marks,
    _not_assessed_subjects,
)
from tests.conftest import auth_headers, get_auth_token


async def _seed_partial(db):
    """Class examined in Maths + Hindi; the student has a Maths mark only."""
    school = School(name="T", code="T", tenant_slug="t", board="CBSE",
                    contact_email="a@t.com", contact_phone="+910000000000", is_active=True)
    db.add(school)
    await db.flush()
    ay = AcademicYear(school_id=school.id, year_label="2026-2027",
                      start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True)
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="1", section="A", academic_year_id=ay.id)
    teach = User(school_id=school.id, mobile="+910000000001", full_name="T",
                 role=UserRole.TEACHER, is_active=True)
    db.add_all([cls, teach])
    await db.flush()
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    hindi = Subject(school_id=school.id, name="Hindi", class_id=cls.id)
    suser = User(school_id=school.id, mobile="+910000000002", full_name="S",
                 role=UserRole.STUDENT, is_active=True)
    db.add_all([maths, hindi, suser])
    await db.flush()
    stu = Student(school_id=school.id, user_id=suser.id, class_id=cls.id, admission_no="A1")
    db.add(stu)
    await db.flush()
    ex_m = Exam(school_id=school.id, class_id=cls.id, subject_id=maths.id,
                exam_type=ExamType.FINAL, title="Maths", total_marks=Decimal("100"),
                date=date(2026, 6, 1), created_by=teach.id)
    ex_h = Exam(school_id=school.id, class_id=cls.id, subject_id=hindi.id,
                exam_type=ExamType.FINAL, title="Hindi", total_marks=Decimal("100"),
                date=date(2026, 6, 1), created_by=teach.id)
    db.add_all([ex_m, ex_h])
    await db.flush()
    # Marks for Maths only — Hindi is left ungraded for this student.
    db.add(ExamMark(school_id=school.id, exam_id=ex_m.id, student_id=stu.id,
                    marks_obtained=Decimal("80")))
    await db.flush()
    return {
        "school_id": school.id,
        "student_id": stu.id,
        "class_id": cls.id,
        "academic_year_id": ay.id,
        "maths_id": maths.id,
        "teach_id": teach.id,
    }


@pytest.mark.asyncio
async def test_not_assessed_surfaces_ungraded_subject(db_session):
    ids = await _seed_partial(db_session)

    consolidated = await _consolidate_marks(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"]
    )
    not_assessed = await _not_assessed_subjects(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"],
        class_id=ids["class_id"],
    )

    assert [s["subject"] for s in consolidated] == ["Maths"]  # only the graded subject
    assert not_assessed == ["Hindi"]                          # the gap is surfaced, not dropped


@pytest.mark.asyncio
async def test_not_assessed_empty_when_all_graded(db_session):
    ids = await _seed_partial(db_session)
    # Grade Hindi too → no gaps.
    hindi_exam = await db_session.execute(
        select(Exam).where(Exam.school_id == ids["school_id"], Exam.title == "Hindi")
    )
    ex_h = hindi_exam.scalar_one()
    db_session.add(ExamMark(school_id=ids["school_id"], exam_id=ex_h.id,
                            student_id=ids["student_id"], marks_obtained=Decimal("70")))
    await db_session.flush()

    not_assessed = await _not_assessed_subjects(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"],
        class_id=ids["class_id"],
    )
    assert not_assessed == []


@pytest.mark.asyncio
async def test_consolidation_can_scope_by_academic_year_and_exam_type(db_session):
    ids = await _seed_partial(db_session)
    old_ay = AcademicYear(
        school_id=ids["school_id"],
        year_label="2025-2026",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 5, 31),
        is_active=False,
    )
    db_session.add(old_ay)
    await db_session.flush()
    old_class = Class(
        school_id=ids["school_id"], grade="1", section="B", academic_year_id=old_ay.id
    )
    db_session.add(old_class)
    await db_session.flush()

    unit_exam = Exam(
        school_id=ids["school_id"], class_id=ids["class_id"], subject_id=ids["maths_id"],
        exam_type=ExamType.UNIT_TEST, title="Unit", total_marks=Decimal("25"),
        date=date(2026, 7, 1), created_by=ids["teach_id"],
    )
    slip_exam = Exam(
        school_id=ids["school_id"], class_id=ids["class_id"], subject_id=ids["maths_id"],
        exam_type=ExamType.SLIP_TEST, title="Slip", total_marks=Decimal("20"),
        date=date(2026, 7, 2), created_by=ids["teach_id"],
    )
    old_exam = Exam(
        school_id=ids["school_id"], class_id=old_class.id, subject_id=ids["maths_id"],
        exam_type=ExamType.FINAL, title="Old year", total_marks=Decimal("100"),
        date=date(2026, 3, 1), created_by=ids["teach_id"],
    )
    db_session.add_all([unit_exam, slip_exam, old_exam])
    await db_session.flush()
    db_session.add_all([
        ExamMark(school_id=ids["school_id"], exam_id=unit_exam.id,
                 student_id=ids["student_id"], marks_obtained=Decimal("20")),
        ExamMark(school_id=ids["school_id"], exam_id=slip_exam.id,
                 student_id=ids["student_id"], marks_obtained=Decimal("15")),
        ExamMark(school_id=ids["school_id"], exam_id=old_exam.id,
                 student_id=ids["student_id"], marks_obtained=Decimal("90")),
    ])
    await db_session.flush()

    current = await _consolidate_marks(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"],
        academic_year_id=ids["academic_year_id"],
    )
    unit = await _consolidate_marks(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"],
        academic_year_id=ids["academic_year_id"], exam_type=ExamType.UNIT_TEST,
    )
    slip = await _consolidate_marks(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"],
        academic_year_id=ids["academic_year_id"], exam_type=ExamType.SLIP_TEST,
    )

    assert current == [{"subject": "Maths", "marks_obtained": 115.0, "total_marks": 145.0}]
    assert unit == [{"subject": "Maths", "marks_obtained": 20.0, "total_marks": 25.0}]
    assert slip == [{"subject": "Maths", "marks_obtained": 15.0, "total_marks": 20.0}]


@pytest.mark.asyncio
async def test_attendance_percentage_can_scope_by_academic_year(db_session):
    ids = await _seed_partial(db_session)
    old_ay = AcademicYear(
        school_id=ids["school_id"], year_label="2025-2026",
        start_date=date(2025, 6, 1), end_date=date(2026, 5, 31), is_active=False,
    )
    db_session.add(old_ay)
    await db_session.flush()
    old_class = Class(
        school_id=ids["school_id"], grade="1", section="B", academic_year_id=old_ay.id
    )
    db_session.add(old_class)
    await db_session.flush()
    db_session.add_all([
        Attendance(school_id=ids["school_id"], student_id=ids["student_id"],
                   class_id=ids["class_id"], date=date(2026, 7, 1),
                   status=AttendanceStatus.PRESENT, marked_by=ids["teach_id"]),
        Attendance(school_id=ids["school_id"], student_id=ids["student_id"],
                   class_id=old_class.id, date=date(2026, 3, 1),
                   status=AttendanceStatus.ABSENT, marked_by=ids["teach_id"]),
    ])
    await db_session.flush()

    from app.modules.ai.services.report_card_service import _attendance_percentage

    current = await _attendance_percentage(
        db_session, school_id=ids["school_id"], student_id=ids["student_id"],
        academic_year_id=ids["academic_year_id"],
    )
    assert current == 100.0


@pytest.mark.asyncio
async def test_generation_rejects_impossible_totals(db_session):
    ids = await _seed_partial(db_session)
    mark = (
        await db_session.execute(
            select(ExamMark).where(ExamMark.student_id == ids["student_id"])
        )
    ).scalar_one()
    mark.marks_obtained = Decimal("-100")
    await db_session.flush()

    from app.modules.ai.services.report_card_service import generate_report_for_student

    with pytest.raises(ValueError, match="outside the valid range"):
        await generate_report_for_student(
            db_session,
            school_id=ids["school_id"],
            created_by=ids["teach_id"],
            student_id=ids["student_id"],
            academic_year_id=ids["academic_year_id"],
        )


@pytest.mark.asyncio
async def test_approval_rejects_persisted_impossible_percentage(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_school: School,
    test_class: Class,
    db_session,
):
    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    report = ReportCard(
        school_id=test_school.id,
        student_id=student.id,
        class_id=test_class.id,
        created_by=admin_user.id,
        title="Invalid legacy card",
        student_name="Test Student",
        class_name="Grade 1 - A",
        subjects=[{"subject": "Maths", "marks_obtained": -100, "total_marks": 20}],
        total_obtained=Decimal("-100"),
        total_max=Decimal("20"),
        percentage=Decimal("-207.78"),
        overall_grade="E",
        status=ReportStatus.DRAFT,
    )
    db_session.add(report)
    await db_session.flush()
    token = await get_auth_token(client, "test_admin", "Admin@123")

    response = await client.post(
        f"/api/v1/ai/report-cards/{report.id}/approve",
        headers=auth_headers(token),
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Report card totals are outside the valid range"
