"""Phase 5: Answer Sheet Evaluation as the SECOND workflow consumer (async + Arq).

Proves the SAME generic workflow model that runs the synchronous Question Paper workflow also
represents and executes the materially different Evaluation workflow — asynchronous, Arq-backed,
with its own domain lifecycle — WITHOUT any evaluation-specific orchestration and WITHOUT
rewriting the evaluation implementation.

Under TESTING the existing `create_and_evaluate` runs the grading synchronously and returns a
`suggested` row (objective answers grade without an LLM), so we can assert the domain-status ->
WorkflowState derivation deterministically. The async ENQUEUE path (pending/QUEUED) is proven by
a direct unit test of the status mapping.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.dependencies import CurrentUser
from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.examination import Exam, ExamType
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.services.question_bank_service import ingest_from_paper
from app.modules.workspace.assistant.planner import PlannerDecision
from app.modules.workspace.workflows import (
    ExecutionMode,
    WorkflowState,
    get_workflow,
    list_workflows,
)
from app.modules.workspace.workflows.executor import (
    WorkflowError,
    _eval_result_block,
    run_workflow,
)

_SECTIONS = [{
    "title": "Section A",
    "instructions": "Answer all.",
    "questions": [
        {"number": "1", "text": "2+2?", "marks": 2, "type": "short", "answer_key": "4"},
        {"number": "2", "text": "Capital?", "marks": 1, "type": "mcq",
         "options": ["Mumbai", "Delhi"], "answer_key": "B"},
    ],
}]


# ── Registration + it is the SAME model as QP ──────────────────────────────────


def test_evaluation_registered_with_generic_model():
    wf = get_workflow("evaluate_answer_sheet")
    assert wf is not None
    assert wf.is_async is True                        # unlike QP (sync)
    assert wf.execution_mode is ExecutionMode.DETERMINISTIC
    assert wf.approval_required is True               # teacher HITL before marks are final
    assert wf.io.input_schema.__name__ == "EvaluationCreate"
    assert wf.io.output_schema.__name__ == "EvaluationOut"
    assert wf.domain_resource == "answer_sheet_evaluation"


def test_both_workflows_share_one_registry():
    ids = {w.workflow_id for w in list_workflows()}
    assert {"question_paper", "evaluate_answer_sheet"} <= ids


# ── Planner mapping (both backends -> same canonical workflow decision) ─────────


def test_jev_evaluation_choice_maps_to_workflow_decision():
    from app.modules.workspace.assistant.jev_planner import _jev_workflow_to_plan

    d = _jev_workflow_to_plan("evaluate_answer_sheet", "grade ARM0218's answer sheet")
    assert isinstance(d, PlannerDecision)
    assert d.action == "workflow"
    assert d.route == "WORKFLOW"
    assert d.workflow_id == "evaluate_answer_sheet"
    assert d.params["student"] == "ARM0218"


# ── Domain status -> WorkflowState mapping (proves the async lifecycle) ─────────


@pytest.mark.parametrize(
    "status,expected",
    [
        ("pending", WorkflowState.QUEUED),
        ("processing", WorkflowState.RUNNING),
        ("suggested", WorkflowState.WAITING_FOR_APPROVAL),
        ("approved", WorkflowState.COMPLETED),
        ("failed", WorkflowState.FAILED),
    ],
)
def test_eval_status_maps_to_workflow_state(status, expected):
    row = SimpleNamespace(
        id=uuid.uuid4(), status=status, job_id=uuid.uuid4(), exam_id=uuid.uuid4(),
        error_message=None,
    )
    block = _eval_result_block(row, exam_title="Unit Test", student_label="Ravi")
    assert block["workflow_state"] == expected.value
    assert block["eval_status"] == status  # domain status stays authoritative


def test_failed_eval_does_not_report_completed():
    row = SimpleNamespace(
        id=uuid.uuid4(), status="failed", job_id=None, exam_id=uuid.uuid4(),
        error_message="ocr failed",
    )
    block = _eval_result_block(row, exam_title="Unit Test", student_label="Ravi")
    assert block["workflow_state"] == WorkflowState.FAILED.value
    assert block["workflow_state"] != WorkflowState.COMPLETED.value


# ── Seed + execution through the generic executor ──────────────────────────────


async def _seed(db):
    school = School(
        name="Eval", code="EV", tenant_slug="test", board="SSC",
        contact_email="a@ev.com", contact_phone="+910000000099", is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    incharge = User(
        school_id=school.id, mobile="+910000000100", full_name="Incharge",
        role=UserRole.CLASS_INCHARGE, is_active=True,
    )
    db.add_all([cls, incharge])
    await db.flush()
    cls.class_incharge_id = incharge.id
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()
    student_user = User(
        school_id=school.id, mobile="+910000000101", full_name="Ravi",
        role=UserRole.STUDENT, is_active=True,
    )
    db.add(student_user)
    await db.flush()
    student = Student(
        school_id=school.id, user_id=student_user.id, class_id=cls.id,
        roll_no="1", admission_no="ADM1",
    )
    db.add(student)
    await db.flush()
    paper = QuestionPaper(
        school_id=school.id, class_id=cls.id, subject_id=maths.id, created_by=incharge.id,
        title="Unit Test", board="SSC", grade="10", subject_name="Maths",
        total_marks=Decimal("3"), duration_minutes=60, topics=["Science"],
        sections=_SECTIONS, status=PaperStatus.APPROVED,
    )
    db.add(paper)
    await db.flush()
    await ingest_from_paper(db, paper, approved_by=incharge.id, approved_at=paper.updated_at)
    exam = Exam(
        school_id=school.id, class_id=cls.id, subject_id=maths.id,
        exam_type=ExamType.UNIT_TEST, title="Unit Test Exam", total_marks=3,
        date=date(2026, 6, 15), created_by=incharge.id, source_paper_id=paper.id,
        question_schema=[
            {"no": "1", "max_marks": 2, "topic": "Science"},
            {"no": "2", "max_marks": 1, "topic": "Science"},
        ],
    )
    db.add(exam)
    await db.flush()
    return SimpleNamespace(
        school=school, cls=cls, subject=maths, student=student, exam=exam, incharge=incharge
    )


def _incharge(seed) -> CurrentUser:
    return CurrentUser(
        id=str(seed.incharge.id), school_id=str(seed.school.id), role="class_incharge",
        tenant_slug="test", full_name="Incharge", mobile="+910000000100",
        is_active=True, jti="j",
    )


@pytest.mark.asyncio
async def test_evaluation_runs_through_generic_executor(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _incharge(seed),
        workflow_id="evaluate_answer_sheet",
        params={
            "exam_id": str(seed.exam.id),
            "student": "ADM1",
            "student_answers": {"1": "4", "2": "B"},
        },
    )
    assert block["kind"] == "workflow"
    assert block["workflow_id"] == "evaluate_answer_sheet"
    # Under TESTING grading runs sync -> suggested -> WAITING_FOR_APPROVAL (teacher HITL).
    assert block["workflow_state"] == WorkflowState.WAITING_FOR_APPROVAL.value
    assert block["eval_status"] == "suggested"
    assert block["summary"]["student"].startswith("Ravi")


@pytest.mark.asyncio
async def test_missing_exam_clarifies(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _incharge(seed),
        workflow_id="evaluate_answer_sheet",
        params={"student": "ADM1"},
    )
    assert block["kind"] == "clarify"


@pytest.mark.asyncio
async def test_missing_answer_source_guides_to_upload(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _incharge(seed),
        workflow_id="evaluate_answer_sheet",
        params={"exam_id": str(seed.exam.id), "student": "ADM1"},
    )
    assert block["kind"] == "guide"
    assert "upload" in block["message"].lower()


@pytest.mark.asyncio
async def test_unauthorized_teacher_rejected(db_session):
    """A subject teacher NOT assigned to this exam's class+subject must be rejected by the
    EXISTING exam authz — the workflow grants nothing."""
    from fastapi import HTTPException

    seed = await _seed(db_session)
    outsider = User(
        school_id=seed.school.id, mobile="+910000000199", full_name="Outsider",
        role=UserRole.TEACHER, is_active=True,
    )
    db_session.add(outsider)
    await db_session.flush()
    user = CurrentUser(
        id=str(outsider.id), school_id=str(seed.school.id), role="teacher",
        tenant_slug="test", full_name="Outsider", mobile="+910000000199",
        is_active=True, jti="j",
    )
    with pytest.raises(HTTPException) as exc:
        await run_workflow(
            db_session, user,
            workflow_id="evaluate_answer_sheet",
            params={
                "exam_id": str(seed.exam.id), "student": "ADM1",
                "student_answers": {"1": "4"},
            },
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_invalid_exam_input_raises_workflow_error(db_session):
    """An exam not linked to an approved paper -> EvalError -> WorkflowError (safe surface)."""
    seed = await _seed(db_session)
    bad_exam = Exam(
        school_id=seed.school.id, class_id=seed.cls.id, subject_id=seed.subject.id,
        exam_type=ExamType.UNIT_TEST, title="No Paper", total_marks=10,
        date=date(2026, 6, 20), created_by=seed.incharge.id,
    )
    db_session.add(bad_exam)
    await db_session.flush()
    with pytest.raises(WorkflowError):
        await run_workflow(
            db_session, _incharge(seed),
            workflow_id="evaluate_answer_sheet",
            params={
                "exam_id": str(bad_exam.id), "student": "ADM1",
                "student_answers": {"1": "4"},
            },
        )
