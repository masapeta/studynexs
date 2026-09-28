"""Phase 6: Lesson Plan as the THIRD workflow consumer (deterministic + approval).

Proves the SAME generic workflow model runs Lesson Planning through the existing lesson-plan
service without a lesson-plan-specific router or any rewrite of the domain logic. Remediation is
deliberately NOT built here (no remediation domain service exists — building it would be inventing
functionality; see the design of record).
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.core.dependencies import CurrentUser
from app.db.models.academic import Class, Subject
from app.db.models.lesson_plan import LessonPlanStatus
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant.planner import PlannerDecision
from app.modules.workspace.workflows import (
    ExecutionMode,
    WorkflowState,
    get_workflow,
    list_workflows,
)
from app.modules.workspace.workflows.executor import run_workflow

# ── Registration + same model ──────────────────────────────────────────────────


def test_lesson_plan_registered_with_generic_model():
    wf = get_workflow("lesson_plan")
    assert wf is not None
    assert wf.execution_mode is ExecutionMode.DETERMINISTIC
    assert wf.is_async is False
    assert wf.approval_required is True
    assert wf.io.input_schema.__name__ == "GenerateLessonPlanRequest"
    assert wf.io.output_schema.__name__ == "LessonPlanOut"
    assert wf.domain_resource == "lesson_plan"


def test_three_workflows_share_one_registry():
    ids = {w.workflow_id for w in list_workflows()}
    assert {"question_paper", "evaluate_answer_sheet", "lesson_plan"} <= ids


def test_jev_lesson_plan_choice_maps_to_workflow_decision():
    from app.modules.workspace.assistant.jev_planner import _jev_workflow_to_plan

    d = _jev_workflow_to_plan("lesson_plan", "plan a 50 mark lesson for class 8 sci")
    assert isinstance(d, PlannerDecision)
    assert d.action == "workflow"
    assert d.workflow_id == "lesson_plan"
    assert d.params["class_label"] == "8"
    assert d.params["subject"] == "science"
    assert "total_marks" not in d.params  # marks are meaningless for a lesson plan


# ── Seed + execution through the generic executor ──────────────────────────────


async def _seed(db, *, incharge_of_class=True):
    school = School(
        name="LP", code="LP", tenant_slug="test", board="SSC",
        contact_email="a@lp.com", contact_phone="+910000000077", is_active=True,
    )
    db.add(school)
    await db.flush()
    from app.db.models.academic import AcademicYear

    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="8", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id, mobile="+910000000078", full_name="Teacher",
        role=UserRole.CLASS_INCHARGE if incharge_of_class else UserRole.TEACHER,
        is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    if incharge_of_class:
        cls.class_incharge_id = teacher.id
    subject = Subject(school_id=school.id, name="Science", class_id=cls.id)
    db.add(subject)
    await db.flush()
    return SimpleNamespace(school=school, cls=cls, subject=subject, teacher=teacher)


def _user(seed) -> CurrentUser:
    role = "class_incharge" if seed.teacher.role == UserRole.CLASS_INCHARGE else "teacher"
    return CurrentUser(
        id=str(seed.teacher.id), school_id=str(seed.school.id), role=role,
        tenant_slug="test", full_name="Teacher", mobile="+910000000078",
        is_active=True, jti="j",
    )


@pytest.mark.asyncio
async def test_lesson_plan_runs_through_generic_executor(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="lesson_plan",
        params={"class_label": "8A", "subject": "Science", "topic": "Photosynthesis"},
    )
    assert block["kind"] == "workflow"
    assert block["workflow_id"] == "lesson_plan"
    assert block["workflow_state"] == WorkflowState.WAITING_FOR_APPROVAL.value
    assert block["plan_status"] == LessonPlanStatus.DRAFT.value  # domain lifecycle authoritative
    assert block["summary"]["topic"] == "Photosynthesis"
    assert block["summary"]["segments"] >= 1


@pytest.mark.asyncio
async def test_missing_class_or_subject_clarifies(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _user(seed), workflow_id="lesson_plan", params={"subject": "Science"}
    )
    assert block["kind"] == "clarify"


@pytest.mark.asyncio
async def test_unknown_class_clarifies(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="lesson_plan",
        params={"class_label": "12Z", "subject": "Science"},
    )
    assert block["kind"] == "clarify"


@pytest.mark.asyncio
async def test_unauthorized_teacher_rejected(db_session):
    """A subject teacher not mapped to teach this class+subject is rejected by the EXISTING gate."""
    from fastapi import HTTPException

    seed = await _seed(db_session, incharge_of_class=False)  # plain teacher, no mapping
    with pytest.raises(HTTPException) as exc:
        await run_workflow(
            db_session, _user(seed),
            workflow_id="lesson_plan",
            params={"class_label": "8A", "subject": "Science"},
        )
    assert exc.value.status_code == 403
