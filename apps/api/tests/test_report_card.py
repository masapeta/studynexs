"""Report-card consolidation: subjects the class was examined in but the student has no
marks for must surface as 'not assessed', not silently vanish. Service-level (no LLM call):
exercises the pure DB helper directly.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.services.report_card_service import (
    _consolidate_marks,
    _not_assessed_subjects,
)


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
    return {"school_id": school.id, "student_id": stu.id, "class_id": cls.id}


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
