"""Answer sheet evaluation v1 — grade, approve, corrections history."""
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.answer_sheet_evaluation import EVAL_STATUS_PROCESSING, AnswerSheetEvaluation
from app.db.models.curriculum_pack import CurriculumPack, PackStatus
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.question_bank import QuestionBankItem, RubricBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.gateway import LLMResult
from app.modules.ai.services.assessment_grounding import GroundingContext
from app.modules.ai.services.question_bank_service import ingest_from_paper
from app.modules.examinations.services.aei_v1_evidence_ledger import (
    contains_unsafe_evidence_key,
)
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
        "academic_year": ay,
        "class": cls,
        "subject": maths,
        "student": student,
        "paper": paper,
        "exam": exam,
        "incharge": incharge,
    }


async def _update_q1_rubric(
    db: AsyncSession,
    *,
    paper: QuestionPaper,
    answer_key: str,
    acceptable_answers: list[str] | None = None,
) -> None:
    rubric = (
        await db.execute(
            select(RubricBankItem)
            .join(
                QuestionBankItem,
                RubricBankItem.question_bank_item_id == QuestionBankItem.id,
            )
            .where(
                QuestionBankItem.source_paper_id == paper.id,
                QuestionBankItem.question_number == "1",
            )
        )
    ).scalar_one()
    rubric.answer_key = answer_key
    rubric.acceptable_answers = acceptable_answers
    await db.flush()


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


@pytest.mark.asyncio
async def test_aei_v1_math_normalization_flag_off_preserves_exact_match(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    await _update_q1_rubric(db_session, paper=fx["paper"], answer_key="0.5")
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_MATH_NORMALIZATION_ENABLED",
        False,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "1/2", "2": "B", "3": "plants use sunlight"},
        },
    )

    assert resp.status_code == 201, resp.text
    suggestion = resp.json()["data"]["ai_suggestions"]["1"]
    assert float(suggestion["marks_suggested"]) == 0
    assert suggestion["method"] == "objective"
    assert "normalized_answer" not in suggestion


@pytest.mark.asyncio
async def test_aei_v1_math_normalization_flag_on_matches_equivalent_answer(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    await _update_q1_rubric(
        db_session,
        paper=fx["paper"],
        answer_key="0.5",
        acceptable_answers=["1/2", "50%", "½"],
    )
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_MATH_NORMALIZATION_ENABLED",
        True,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "1/2", "2": "B", "3": "plants use sunlight"},
        },
    )

    assert resp.status_code == 201, resp.text
    suggestion = resp.json()["data"]["ai_suggestions"]["1"]
    assert float(suggestion["marks_suggested"]) == 2
    assert suggestion["method"] == "aei_v1_math_normalization"
    assert suggestion["normalized_answer"] == "0.5"
    assert suggestion["manual_review_required"] is False


@pytest.mark.asyncio
async def test_aei_v1_review_policy_flag_on_adds_review_metadata(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_REVIEW_POLICY_ENABLED",
        True,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants use sunlight"},
        },
    )

    assert resp.status_code == 201, resp.text
    suggestion = resp.json()["data"]["ai_suggestions"]["1"]
    assert suggestion["manual_review_required"] is False
    assert suggestion["manual_review_reason"] is None
    assert suggestion["capability_mode"] == "supported"
    assert suggestion["confidence_reason"] == "Confidence meets the teacher-review threshold."
    assert suggestion["aei_v1_review_policy"]["batch"] == "B"


@pytest.mark.asyncio
async def test_aei_v1_review_policy_requires_override_reason_when_enabled(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_REVIEW_POLICY_ENABLED",
        True,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants use sunlight"},
        },
    )
    assert resp.status_code == 201, resp.text
    eval_id = resp.json()["data"]["id"]

    missing_reason = await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={"teacher_overrides": {"1": {"marks": 1}}},
    )
    assert missing_reason.status_code == 400
    assert "requires a non-empty reason" in missing_reason.text

    approved = await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={
            "teacher_overrides": {
                "1": {"marks": 1, "reason": "Teacher reviewed working."}
            }
        },
    )
    assert approved.status_code == 200, approved.text
    override = approved.json()["data"]["teacher_overrides"]["1"]
    audit = override["aei_v1_override_audit"]
    assert audit["batch"] == "B"
    assert audit["override_applied"] is True
    assert audit["original_marks_suggested"] == 2
    assert audit["final_marks"] == 1


@pytest.mark.asyncio
async def test_aei_v1_language_ocr_assist_flag_off_preserves_suggestions(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED",
        False,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants use sunlight"},
        },
    )

    assert resp.status_code == 201, resp.text
    suggestion = resp.json()["data"]["ai_suggestions"]["1"]
    assert "aei_v1_language_ocr_assist" not in suggestion
    assert "answer_language" not in suggestion


@pytest.mark.asyncio
async def test_aei_v1_language_ocr_assist_flag_on_adds_language_review_metadata(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    fx["subject"].name = "Hindi"
    fx["paper"].subject_name = "Hindi"
    await db_session.flush()
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED",
        True,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "उत्तर", "2": "B", "3": "उत्तर"},
        },
    )

    assert resp.status_code == 201, resp.text
    suggestion = resp.json()["data"]["ai_suggestions"]["1"]
    assist = suggestion["aei_v1_language_ocr_assist"]
    assert suggestion["answer_language"] == "Hindi"
    assert suggestion["detected_script"] == "Devanagari"
    assert suggestion["answer_input_source"] == "teacher_text"
    assert suggestion["manual_review_required"] is True
    assert suggestion["requires_language_teacher_review"] is True
    assert assist["autonomous_language_grading"] is False
    assert assist["assist_only"] is True


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
async def test_eval_response_exposes_academic_evidence_ledger(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    fx = await _seed_eval_fixture(db_session)
    pack = CurriculumPack(
        school_id=fx["school"].id,
        class_id=fx["class"].id,
        subject_id=fx["subject"].id,
        academic_year_id=fx["academic_year"].id,
        board="SSC",
        book_title="Traceable Maths Pack",
        created_by=fx["incharge"].id,
        status=PackStatus.APPROVED,
        approved_by=fx["incharge"].id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(pack)
    await db_session.flush()
    fx["paper"].pack_id = pack.id
    fx["paper"].grounded = True
    fx["paper"].grounding_sources = [
        {
            "index": 1,
            "chapter": "Quadratic Equations",
            "topic": "Quadratic Equations",
            "ref_id": "trace-topic-1",
        }
    ]
    await db_session.flush()

    async def _fake_grounding(*_args, **_kwargs):
        return GroundingContext(
            context_text="[1] Quadratic Equations: factorisation and roots.",
            sources=[
                {
                    "index": 1,
                    "chapter": "Quadratic Equations",
                    "topic": "Quadratic Equations",
                    "ref_id": "trace-topic-1",
                }
            ],
        )

    async def _fake_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps({
                "evaluations": [
                    {
                        "number": "3",
                        "criteria": [
                            {
                                "criterion": "Uses the core process",
                                "max_points": 3,
                                "awarded_points": 2,
                                "met": False,
                            }
                        ],
                        "marks_suggested": 2,
                        "feedback": "Partially correct.",
                        "confidence": 0.8,
                        "citations": [1],
                    }
                ]
            }),
            provider="stub",
            model="stub-model",
            tokens_in=12,
            tokens_out=34,
            latency_ms=1,
        )

    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service.ground_for_evaluation",
        _fake_grounding,
    )
    monkeypatch.setattr("app.modules.ai.services.evaluation_engine.generate_llm", _fake_llm)

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {
                "1": "4",
                "2": "B",
                "3": "plants use sunlight",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["question_paper_id"] == str(fx["paper"].id)
    assert data["curriculum_pack_id"] == str(pack.id)
    assert data["question_paper_grounded"] is True
    assert data["evaluation_grounded"] is True
    assert "trace-topic-1" in data["citation_ids"]
    assert data["evidence_ledger"]["question_paper_id"] == str(fx["paper"].id)
    assert data["evidence_ledger"]["curriculum_pack_id"] == str(pack.id)
    assert data["ai_suggestions"]["3"]["grounded"] is True
    assert data["ai_suggestions"]["3"]["grounding_sources"][0]["ref_id"] == "trace-topic-1"

    approve = await client.post(
        f"/api/v1/exams/evaluations/{data['id']}/approve",
        headers=auth_headers(token),
        json={},
    )
    assert approve.status_code == 200, approve.text
    approved = approve.json()["data"]
    assert approved["status"] == "approved"
    assert approved["evidence_ledger"]["teacher_approved_by"] == str(fx["incharge"].id)
    assert approved["evidence_ledger"]["teacher_approved_at"]

    corr = await client.get(
        f"/api/v1/exams/corrections?class_id={fx['class'].id}",
        headers=auth_headers(token),
    )
    assert corr.status_code == 200, corr.text
    row = next(r for r in corr.json()["data"] if r["question_no"] == "3")
    assert row["question_paper_id"] == str(fx["paper"].id)
    assert row["curriculum_pack_id"] == str(pack.id)
    assert row["evaluation_grounded"] is True
    assert "trace-topic-1" in row["citation_ids"]


@pytest.mark.asyncio
async def test_aei_v1_evidence_ledger_flag_off_preserves_legacy_ledger(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    fx = await _seed_eval_fixture(db_session)
    monkeypatch.setattr(
        "app.modules.examinations.endpoints.evaluation"
        ".settings.AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED",
        False,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants use sunlight"},
        },
    )

    assert resp.status_code == 201, resp.text
    ledger = resp.json()["data"]["evidence_ledger"]
    assert "aei_v1_approved_evidence" not in ledger


@pytest.mark.asyncio
async def test_aei_v1_evidence_ledger_flag_on_emits_approved_evidence_after_teacher_approval(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    fx = await _seed_eval_fixture(db_session)
    monkeypatch.setattr(
        "app.modules.examinations.endpoints.evaluation"
        ".settings.AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_REVIEW_POLICY_ENABLED",
        True,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants use sunlight"},
        },
    )
    assert resp.status_code == 201, resp.text
    suggested = resp.json()["data"]
    suggested_metadata = suggested["evidence_ledger"]["aei_v1_approved_evidence"]
    assert suggested_metadata["approved_evidence"] is False
    assert suggested_metadata["approved_for_downstream"] is False
    assert suggested_metadata["questions"] == {}

    approved = await client.post(
        f"/api/v1/exams/evaluations/{suggested['id']}/approve",
        headers=auth_headers(token),
        json={
            "teacher_overrides": {
                "1": {"marks": 1, "reason": "Teacher reviewed alternate working."}
            },
        },
    )

    assert approved.status_code == 200, approved.text
    metadata = approved.json()["data"]["evidence_ledger"]["aei_v1_approved_evidence"]
    assert metadata["approved_evidence"] is True
    assert metadata["approved_for_downstream"] is True
    assert metadata["teacher_approved_by"] == str(fx["incharge"].id)
    assert metadata["question_count"] == 3
    assert metadata["override_count"] == 1
    assert metadata["manual_review_required_count"] == sum(
        1
        for question in metadata["questions"].values()
        if question["original_suggestion"].get("manual_review_required")
    )
    assert metadata["downstream_contract"]["source_of_truth"] == "teacher_decision"

    q1 = metadata["questions"]["1"]
    assert q1["original_suggestion"]["marks_suggested"] == 2
    assert q1["final_teacher_decision"]["final_marks"] == 1
    assert q1["final_teacher_decision"]["override_applied"] is True
    assert q1["final_teacher_decision"]["override_reason"] == (
        "Teacher reviewed alternate working."
    )
    assert contains_unsafe_evidence_key(metadata) is False


@pytest.mark.asyncio
async def test_eval_approval_recovers_cleanly_after_invalid_override(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _seed_eval_fixture(db_session)
    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "4", "2": "B", "3": "plants use sunlight"},
        },
    )
    assert resp.status_code == 201, resp.text
    eval_id = resp.json()["data"]["id"]

    bad = await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={"teacher_overrides": {"3": {"marks": 99, "reason": "bad input"}}},
    )
    assert bad.status_code == 400

    row = await AnswerSheetEvalService(db_session).get_evaluation(
        fx["school"].id, uuid.UUID(eval_id)
    )
    assert row is not None
    assert row.status == "suggested"
    marks = (
        await db_session.execute(
            select(ExamMark).where(
                ExamMark.exam_id == fx["exam"].id,
                ExamMark.student_id == fx["student"].id,
            )
        )
    ).scalar_one_or_none()
    assert marks is None

    good = await client.post(
        f"/api/v1/exams/evaluations/{eval_id}/approve",
        headers=auth_headers(token),
        json={"teacher_overrides": {"3": {"marks": 2, "reason": "reviewed"}}},
    )
    assert good.status_code == 200, good.text
    assert good.json()["data"]["status"] == "approved"


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
            "student_answers": {
                "1": "4",
                "2": "B",
                "3": "full answer about photosynthesis plants food sunlight",
            },
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
