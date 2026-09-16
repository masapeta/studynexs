"""Exam / marks capabilities (Phase 5 / P1).

Grounded strictly in the audited schema (Exam + ExamMark). These tests assert the
capabilities read real marks correctly, compute percentage as marks/total, surface the
STORED grade letter without inventing pass/fail, and rank correctly — the semantic
primitives student+exam+subject+marks+grade+ranking, with no invented "term" concept.
"""

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant import capabilities as cap


class _FakeUser:
    def __init__(self, school_id, role="super_admin"):
        self.school_id = str(school_id)
        self.role = role
        self.id = str(school_id)


@pytest_asyncio.fixture
async def exam_setup(db_session: AsyncSession, test_school: School, test_class: Class):
    """Two students in one class, one subject, one exam, distinct marks."""
    # Subject is per-class.
    subject = Subject(school_id=test_school.id, name="Mathematics", class_id=test_class.id)
    db_session.add(subject)
    await db_session.flush()

    students = []
    for i, (adm, name, marks, grade) in enumerate(
        [("ADM100", "Asha Rao", Decimal("82.00"), "A"),
         ("ADM101", "Ravi Kumar", Decimal("40.00"), "D")]
    ):
        u = User(
            school_id=test_school.id, username=f"stu{i}", mobile=f"+9199999900{i}0",
            full_name=name, role=UserRole.STUDENT, password_hash="x", is_active=True,
        )
        db_session.add(u)
        await db_session.flush()
        s = Student(
            school_id=test_school.id, user_id=u.id, class_id=test_class.id,
            admission_no=adm, roll_no=str(i + 1),
        )
        db_session.add(s)
        await db_session.flush()
        students.append((s, marks, grade))

    exam = Exam(
        school_id=test_school.id, class_id=test_class.id, subject_id=subject.id,
        exam_type=ExamType.MID_TERM, title="Mid Term — Mathematics",
        total_marks=Decimal("100.00"), date=date(2026, 9, 1),
        created_by=students[0][0].user_id,
    )
    db_session.add(exam)
    await db_session.flush()
    for s, marks, grade in students:
        db_session.add(ExamMark(
            school_id=test_school.id, exam_id=exam.id, student_id=s.id,
            marks_obtained=marks, grade_letter=grade,
        ))
    await db_session.flush()
    return {"class": test_class, "subject": subject, "exam": exam, "students": students}


@pytest.mark.asyncio
async def test_student_marks_reads_real_marks(
    test_school: School, exam_setup, db_session: AsyncSession
):
    user = _FakeUser(test_school.id)
    block = await cap.student_marks(db_session, user, {"student": "ADM100"})
    assert block["kind"] == "table"
    assert len(block["rows"]) == 1
    row = block["rows"][0]
    assert row["obtained"] == 82.0
    assert row["total"] == 100.0
    assert row["percentage"] == 82.0  # marks/total, not invented
    assert row["grade"] == "A"  # the STORED grade letter
    assert row["subject"] == "Mathematics"


@pytest.mark.asyncio
async def test_student_marks_subject_filter(
    test_school: School, exam_setup, db_session: AsyncSession
):
    user = _FakeUser(test_school.id)
    block = await cap.student_marks(db_session, user, {"student": "ADM100", "subject": "Mathematics"})
    assert block["kind"] == "table"
    assert all(r["subject"] == "Mathematics" for r in block["rows"])
    # An unknown subject is honest, not empty-invented.
    miss = await cap.student_marks(db_session, user, {"student": "ADM100", "subject": "Biology"})
    assert miss["kind"] == "not_found"


@pytest.mark.asyncio
async def test_student_marks_not_found(
    test_school: School, exam_setup, db_session: AsyncSession
):
    user = _FakeUser(test_school.id)
    block = await cap.student_marks(db_session, user, {"student": "NOPE999"})
    assert block["kind"] == "not_found"


@pytest.mark.asyncio
async def test_subject_toppers_ranks_by_marks(
    test_school: School, exam_setup, db_session: AsyncSession
):
    user = _FakeUser(test_school.id)
    cls = exam_setup["class"]
    label = f"{cls.grade} {cls.section}"
    block = await cap.subject_toppers(
        db_session, user, {"class_label": label, "subject": "Mathematics"}
    )
    assert block["kind"] == "table"
    # Highest first by default.
    assert block["rows"][0]["obtained"] == 82.0
    assert block["rows"][-1]["obtained"] == 40.0
    # bottom 1 -> lowest scorer.
    bottom = await cap.subject_toppers(
        db_session, user, {"class_label": label, "subject": "Mathematics", "bottom": 1}
    )
    assert len(bottom["rows"]) == 1
    assert bottom["rows"][0]["obtained"] == 40.0


@pytest.mark.asyncio
async def test_subject_toppers_requires_both(
    test_school: School, exam_setup, db_session: AsyncSession
):
    user = _FakeUser(test_school.id)
    block = await cap.subject_toppers(db_session, user, {"class_label": "10A"})
    assert block["kind"] == "clarify"


@pytest.mark.asyncio
async def test_class_results_matrix_and_ranking(
    test_school: School, exam_setup, db_session: AsyncSession
):
    user = _FakeUser(test_school.id)
    cls = exam_setup["class"]
    label = f"{cls.grade} {cls.section}"
    block = await cap.class_results(db_session, user, {"class_label": label})
    assert block["kind"] == "table"
    assert len(block["rows"]) == 2
    # top 1 -> the higher average student (Asha, 82%).
    top = await cap.class_results(db_session, user, {"class_label": label, "top": 1})
    assert len(top["rows"]) == 1
    assert top["rows"][0]["name"] == "Asha Rao"
    assert top["rows"][0]["average"] == 82.0


@pytest.mark.asyncio
async def test_class_results_no_marks_is_honest(
    test_school: School, test_class: Class, db_session: AsyncSession
):
    """A class with students but no exams must not fabricate results."""
    # Give the class a student but no exams.
    u = User(
        school_id=test_school.id, username="lonely", mobile="+919111111111",
        full_name="No Marks", role=UserRole.STUDENT, password_hash="x", is_active=True,
    )
    db_session.add(u)
    await db_session.flush()
    db_session.add(Student(
        school_id=test_school.id, user_id=u.id, class_id=test_class.id,
        admission_no="ADM900", roll_no="9",
    ))
    await db_session.flush()
    user = _FakeUser(test_school.id)
    block = await cap.class_results(
        db_session, user, {"class_label": f"{test_class.grade} {test_class.section}"}
    )
    # Students exist but no marks -> matrix with empty subject set, averages None.
    assert block["kind"] == "table"
    assert all(r["average"] is None for r in block["rows"])


# ── Composition: exam average enricher + filter + ranking ─────────────────────


@pytest.mark.asyncio
async def test_composition_exam_average_enricher(
    test_school: School, exam_setup, db_session: AsyncSession
):
    from app.modules.workspace.assistant.composition import execute_plan, parse_plan
    from app.modules.workspace.assistant.temporal import resolve_time_range

    async def rng(_sid, tok):
        return await resolve_time_range(db_session, test_school, test_school.id, tok)

    cls = exam_setup["class"]
    label = f"{cls.grade} {cls.section}"
    plan = parse_plan({
        "operations": [
            {"id": "s", "capability": "class_students", "params": {"class_label": label}},
            {"id": "e", "capability": "enrich_exam_average", "depends_on": ["s"]},
            {"id": "f", "capability": "filter", "depends_on": ["e"],
             "filters": [{"field": "exam_average", "op": "<", "value": 50}]},
        ],
        "output": {"columns": ["admission_no", "name", "exam_average"], "sort_field": "exam_average"},
    })
    user = _FakeUser(test_school.id)
    result = await execute_plan(db_session, user, plan, resolve_range=rng)
    # Only Ravi (40%) is below 50; Asha (82%) filtered out.
    assert len(result.rows) == 1
    assert result.rows[0]["name"] == "Ravi Kumar"
    assert result.rows[0]["exam_average"] == 40.0
