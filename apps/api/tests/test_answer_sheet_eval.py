"""Answer sheet evaluation v1 — grade, approve, corrections history."""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.services.question_bank_service import ingest_from_paper
from app.modules.examinations.services.answer_sheet_eval_service import (
    AnswerSheetEvalService,
    grade_objective,
    grade_subjective_heuristic,
)
from tests.conftest import access_token_for, auth_headers

SECTIONS = [
    {
        "title": "Section A",
        "instructions": "Answer all.",
        "questions": [
            {
                "number": "1",
                "text": "What is 2+2?",
                "marks": 2,
                "type": "short",
                "answer_key": "4",
            },
            {
                "number": "2",
                "text": "Capital of India?",
                "marks": 1,
                "type": "mcq",
                "options": ["Mumbai", "Delhi", "Kolkata", "Chennai"],
                "answer_key": "B",
            },
            {
                "number": "3",
                "text": "Define photosynthesis.",
                "marks": 3,
                "type": "long",
                "answer_key": "Process by which plants make food using sunlight.",
            },
        ],
    },
]


async def _seed_eval_fixture(db: AsyncSession):
    school = School(
        name="Eval School",
        code="EV",
        tenant_slug="test",
        board="SSC",
        contact_email="a@ev.com",
        contact_phone="+910000000099",
        is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    incharge = User(
        school_id=school.id,
        mobile="+910000000100",
        full_name="Incharge",
        role=UserRole.CLASS_INCHARGE,
        is_active=True,
    )
    db.add_all([cls, incharge])
    await db.flush()
    cls.class_incharge_id = incharge.id
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()
    student_user = User(
        school_id=school.id,
        mobile="+910000000101",
        full_name="Ravi",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(student_user)
    await db.flush()
    student = Student(
        school_id=school.id,
        user_id=student_user.id,
        class_id=cls.id,
        roll_no="1",
        admission_no="ADM1",
    )
    db.add(student)
    await db.flush()
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        created_by=incharge.id,
        title="Unit Test",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=Decimal("6"),
        duration_minutes=60,
        topics=["Science"],
        sections=SECTIONS,
        status=PaperStatus.APPROVED,
    )
    db.add(paper)
    await db.flush()
    await ingest_from_paper(
        db, paper, approved_by=incharge.id, approved_at=paper.updated_at
    )
    exam = Exam(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        exam_type=ExamType.UNIT_TEST,
        title="Unit Test Exam",
        total_marks=6,
        date=date(2026, 6, 15),
        created_by=incharge.id,
        source_paper_id=paper.id,
        question_schema=[
            {"no": "1", "max_marks": 2, "topic": "Science"},
            {"no": "2", "max_marks": 1, "topic": "Science"},
            {"no": "3", "max_marks": 3, "topic": "Science"},
        ],
    )
    db.add(exam)
    await db.flush()
    return {
        "school": school,
        "class": cls,
        "subject": maths,
        "student": student,
        "paper": paper,
        "exam": exam,
        "incharge": incharge,
    }


def test_grade_objective_mcq():
    marks, feedback, conf = grade_objective(
        q_type="mcq",
        student_answer="Delhi",
        answer_key="B",
        max_marks=1,
        options=["Mumbai", "Delhi", "Kolkata", "Chennai"],
    )
    assert marks == 1
    assert conf > 0.9


def test_grade_objective_wrong():
    marks, _, _ = grade_objective(
        q_type="short",
        student_answer="5",
        answer_key="4",
        max_marks=2,
    )
    assert marks == 0


def test_grade_subjective_partial():
    marks, feedback, _ = grade_subjective_heuristic(
        student_answer="plants make food using sunlight",
        answer_key="Process by which plants make food using sunlight.",
        max_marks=3,
    )
    assert marks >= 1.5
    assert "match" in feedback.lower()


@pytest.mark.asyncio
async def test_eval_create_and_approve(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _seed_eval_fixture(db_session)
    token = access_token_for(fx["incharge"])
    exam_id = str(fx["exam"].id)
    student_id = str(fx["student"].id)

    resp = await client.post(
        f"/api/v1/exams/{exam_id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": student_id,
            "student_answers": {
                "1": "4",
                "2": "B",
                "3": "plants use sunlight to make food",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["status"] == "suggested"
    assert float(data["ai_suggestions"]["1"]["marks_suggested"]) == 2
    assert float(data["ai_suggestions"]["2"]["marks_suggested"]) == 1

    eval_id = data["id"]
    resp = await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={
            "teacher_overrides": {"3": {"marks": 2, "reason": "Partial credit"}},
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "approved"

    marks = (
        await db_session.execute(
            select(ExamMark).where(
                ExamMark.exam_id == fx["exam"].id,
                ExamMark.student_id == fx["student"].id,
            )
        )
    ).scalar_one()
    assert float(marks.marks_obtained) == 5  # 2 + 1 + 2
    assert marks.ai_graded is True
    assert marks.question_marks["3"] == 2


@pytest.mark.asyncio
async def test_corrections_history(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _seed_eval_fixture(db_session)
    token = access_token_for(fx["incharge"])
    exam_id = str(fx["exam"].id)

    await client.post(
        f"/api/v1/exams/{exam_id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "full answer about photosynthesis plants food sunlight"},
        },
    )
    eval_id = (
        await client.get(
            f"/api/v1/exams/{exam_id}/evaluations",
            headers=auth_headers(token),
        )
    ).json()["data"][0]["id"]

    await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={},
    )

    resp = await client.get(
        f"/api/v1/exams/corrections?class_id={fx['class'].id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()["data"]
    assert len(rows) >= 3
    q3 = next(r for r in rows if r["question_no"] == "3")
    assert q3["teacher_marks"] == q3["ai_marks"]


@pytest.mark.asyncio
async def test_misconceptions_extracted_on_approve(
    client: AsyncClient, db_session: AsyncSession
):
    from app.db.models.misconception import MisconceptionEntry

    fx = await _seed_eval_fixture(db_session)
    token = access_token_for(fx["incharge"])
    exam_id = str(fx["exam"].id)

    resp = await client.post(
        f"/api/v1/exams/{exam_id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "5", "2": "A", "3": "wrong"},
        },
    )
    assert resp.status_code == 201
    eval_id = resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={},
    )

    rows = (
        await db_session.execute(
            select(MisconceptionEntry).where(
                MisconceptionEntry.school_id == fx["school"].id
            )
        )
    ).scalars().all()
    assert len(rows) >= 2

    lib = await client.get(
        f"/api/v1/exams/misconceptions?class_id={fx['class'].id}",
        headers=auth_headers(token),
    )
    assert lib.status_code == 200
    assert len(lib.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_eval_requires_linked_paper(
    client: AsyncClient, db_session: AsyncSession, test_school, test_class, admin_user
):
    from app.db.models.academic import Subject
    from tests.conftest import get_auth_token

    subject = Subject(school_id=test_school.id, name="Sci", class_id=test_class.id)
    db_session.add(subject)
    await db_session.flush()
    exam = Exam(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        exam_type=ExamType.QUIZ,
        title="No paper",
        total_marks=10,
        created_by=admin_user.id,
        question_schema=[{"no": "1", "max_marks": 10}],
    )
    db_session.add(exam)
    student_user = User(
        school_id=test_school.id,
        mobile="+919876543299",
        full_name="S",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(student_user)
    await db_session.flush()
    student = Student(
        school_id=test_school.id,
        user_id=student_user.id,
        class_id=test_class.id,
        roll_no="9",
        admission_no="X",
    )
    db_session.add(student)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        f"/api/v1/exams/{exam.id}/evaluations",
        headers=auth_headers(token),
        json={"student_id": str(student.id), "student_answers": {"1": "x"}},
    )
    assert resp.status_code == 400
    assert "paper" in resp.json()["detail"].lower()


async def _science_only_teacher(db: AsyncSession, fx: dict) -> User:
    from app.db.models.academic import TeacherSubjectMapping

    science = Subject(
        school_id=fx["school"].id,
        class_id=fx["class"].id,
        name="Science",
        code="SCI",
    )
    db.add(science)
    await db.flush()
    teacher = User(
        school_id=fx["school"].id,
        mobile="+910000000200",
        full_name="Science Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(teacher)
    await db.flush()
    db.add(
        TeacherSubjectMapping(
            school_id=fx["school"].id,
            teacher_id=teacher.id,
            subject_id=science.id,
            class_id=fx["class"].id,
            is_primary=True,
        )
    )
    await db.flush()
    return teacher


@pytest.mark.asyncio
async def test_teacher_cannot_see_other_subject_corrections(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _seed_eval_fixture(db_session)
    incharge_token = access_token_for(fx["incharge"])
    exam_id = str(fx["exam"].id)

    await client.post(
        f"/api/v1/exams/{exam_id}/evaluations",
        headers=auth_headers(incharge_token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants food sunlight"},
        },
    )
    eval_id = (
        await client.get(
            f"/api/v1/exams/{exam_id}/evaluations",
            headers=auth_headers(incharge_token),
        )
    ).json()["data"][0]["id"]
    await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(incharge_token),
        json={},
    )

    science_teacher = await _science_only_teacher(db_session, fx)
    science_token = access_token_for(science_teacher)
    resp = await client.get(
        f"/api/v1/exams/corrections?class_id={fx['class'].id}",
        headers=auth_headers(science_token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_teacher_cannot_see_other_subject_misconceptions(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _seed_eval_fixture(db_session)
    incharge_token = access_token_for(fx["incharge"])
    exam_id = str(fx["exam"].id)

    await client.post(
        f"/api/v1/exams/{exam_id}/evaluations",
        headers=auth_headers(incharge_token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "5", "2": "A", "3": "wrong"},
        },
    )
    eval_id = (
        await client.get(
            f"/api/v1/exams/{exam_id}/evaluations",
            headers=auth_headers(incharge_token),
        )
    ).json()["data"][0]["id"]
    await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(incharge_token),
        json={},
    )

    science_teacher = await _science_only_teacher(db_session, fx)
    science_token = access_token_for(science_teacher)
    resp = await client.get(
        f"/api/v1/exams/misconceptions?class_id={fx['class'].id}",
        headers=auth_headers(science_token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_eval_reject_while_processing(
    client: AsyncClient, db_session: AsyncSession
):
    from app.db.models.answer_sheet_evaluation import (
        AnswerSheetEvaluation,
        EVAL_STATUS_PROCESSING,
    )

    fx = await _seed_eval_fixture(db_session)
    token = access_token_for(fx["incharge"])
    db_session.add(
        AnswerSheetEvaluation(
            school_id=fx["school"].id,
            exam_id=fx["exam"].id,
            student_id=fx["student"].id,
            created_by=fx["incharge"].id,
            status=EVAL_STATUS_PROCESSING,
            input_answers={"1": "4"},
        )
    )
    await db_session.flush()

    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B"},
        },
    )
    assert resp.status_code == 400
    assert "in progress" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_eval_does_not_double_charge_credits(
    client: AsyncClient, db_session: AsyncSession
):
    from app.db.models.ai_usage import AIUsage

    fx = await _seed_eval_fixture(db_session)
    token = access_token_for(fx["incharge"])
    exam_id = str(fx["exam"].id)
    student_id = str(fx["student"].id)

    resp = await client.post(
        f"/api/v1/exams/{exam_id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": student_id,
            "student_answers": {"1": "4", "2": "B", "3": "plants sunlight food"},
        },
    )
    assert resp.status_code == 201
    eval_id = resp.json()["data"]["id"]

    service = AnswerSheetEvalService(db_session)
    await service.execute_evaluation(uuid.UUID(eval_id), role="class_incharge")

    usage_rows = (
        await db_session.execute(
            select(AIUsage).where(
                AIUsage.ref_type == "answer_sheet_evaluation",
                AIUsage.ref_id == uuid.UUID(eval_id),
                AIUsage.credits_charged > 0,
            )
        )
    ).scalars().all()
    assert len(usage_rows) == 1
