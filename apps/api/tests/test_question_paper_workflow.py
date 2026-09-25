"""Phase 4: Question Paper routed through the assistant as the first workflow consumer.

These tests prove the generic workflow pattern works end to end for QP WITHOUT a QP-specific
router and WITHOUT rewriting QP domain logic:
  planner (Gemma/JEV) -> PlannerDecision(action="workflow") -> WorkflowRegistry -> executor ->
  existing QP service (mocked here; it has its own tests) + existing authorization + approved
  pack lookup -> structured result.

Generation internals are covered by test_question_paper*.py; here we mock `generate_paper` at
the executor boundary and assert the WIRING: routing, param extraction, authorization, the
approved-pack gate, clarify/unknown handling, and that the QP domain lifecycle stays authoritative.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core.dependencies import CurrentUser
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.curriculum_pack import CurriculumPack, PackStatus
from app.db.models.question_paper import PaperStatus
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant.planner import PlannerDecision
from app.modules.workspace.workflows import get_workflow
from app.modules.workspace.workflows.executor import WorkflowError, run_workflow

# ── Planner mapping: both backends produce the SAME canonical workflow decision ────


def test_jev_workflow_choice_maps_to_workflow_decision():
    from app.modules.workspace.assistant.jev_planner import _jev_workflow_to_plan

    # Uses a colloquial alias ("sci") — the SAME deterministic subject extractor the JEV
    # capability path uses. Canonical subject names ("Science") are resolved downstream by the
    # executor's resolve_subject against the school's real subjects, not pre-extracted here.
    d = _jev_workflow_to_plan("question_paper", "make a 50 mark sci paper for class 8")
    assert isinstance(d, PlannerDecision)
    assert d.action == "workflow"
    assert d.route == "WORKFLOW"
    assert d.workflow_id == "question_paper"
    assert d.params["class_label"] == "8"
    assert d.params["subject"] == "science"
    assert d.params["total_marks"] == 50


def test_workflow_decision_is_not_a_capability():
    """A workflow must not be represented as a tool (it is not a capability)."""
    d = PlannerDecision(
        action="workflow", route="WORKFLOW", workflow_id="question_paper", params={}
    )
    assert d.tool is None
    assert d.action != "tool"


# ── Seed helpers ───────────────────────────────────────────────────────────────


async def _seed(db, *, with_pack=True, teacher_maps=True):
    school = School(
        name="T", code="T", tenant_slug="test", board="SSC",
        contact_email="a@t.com", contact_phone="+910000000000", is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="8", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id, mobile="+910000000001", full_name="T",
        role=UserRole.TEACHER, is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    subject = Subject(school_id=school.id, name="Science", class_id=cls.id)
    db.add(subject)
    await db.flush()
    if teacher_maps:
        db.add(
            TeacherSubjectMapping(
                school_id=school.id, teacher_id=teacher.id,
                class_id=cls.id, subject_id=subject.id,
            )
        )
        await db.flush()
    if with_pack:
        pack = CurriculumPack(
            school_id=school.id, class_id=cls.id, subject_id=subject.id,
            academic_year_id=ay.id, board="SSC", version=1, created_by=teacher.id,
            status=PackStatus.APPROVED,
        )
        db.add(pack)
        await db.flush()
    return SimpleNamespace(school=school, cls=cls, subject=subject, teacher=teacher)


def _user(seed) -> CurrentUser:
    return CurrentUser(
        id=str(seed.teacher.id), school_id=str(seed.school.id), role="teacher",
        tenant_slug="test", full_name="T", mobile="+910000000001",
        is_active=True, jti="j",
    )


def _fake_paper(seed):
    return SimpleNamespace(
        id=uuid.uuid4(), total_marks=Decimal("50"), status=PaperStatus.DRAFT,
        grounded=True,
        sections=[SimpleNamespace(questions=[object(), object(), object()])],
    )


# ── Executor: registry resolution + success path (QP service mocked) ───────────


@pytest.mark.asyncio
async def test_registry_resolves_question_paper():
    wf = get_workflow("question_paper")
    assert wf is not None and wf.workflow_id == "question_paper"


@pytest.mark.asyncio
async def test_workflow_success_returns_structured_result(db_session, monkeypatch):
    seed = await _seed(db_session)
    captured = {}

    async def _fake_generate(db, **kwargs):
        captured.update(kwargs)
        return _fake_paper(seed)

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _fake_generate
    )
    # credit cap is not the unit under test — stub it to a fixed cost.
    monkeypatch.setattr(
        "app.modules.ai.services.usage_caps.enforce_monthly_ai_cap",
        lambda *a, **k: _acoro(1),
    )

    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="question_paper",
        params={"class_label": "8A", "subject": "Science", "total_marks": 50},
    )
    assert block["kind"] == "workflow"
    assert block["workflow_id"] == "question_paper"
    assert block["workflow_state"] == "waiting_for_approval"
    assert block["paper_status"] == "draft"  # QP domain lifecycle stays authoritative
    assert block["summary"]["question_count"] == 3
    assert block["summary"]["total_marks"] == 50.0
    # The executor called the EXISTING QP service with resolved ids + the approved pack.
    assert captured["class_id"] == seed.cls.id
    assert captured["subject_id"] == seed.subject.id
    assert captured["pack_id"] is not None
    assert captured["total_marks"] == 50


@pytest.mark.asyncio
async def test_missing_class_or_subject_clarifies(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _user(seed), workflow_id="question_paper", params={"subject": "Science"}
    )
    assert block["kind"] == "clarify"


@pytest.mark.asyncio
async def test_unknown_workflow_degrades_to_guide(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _user(seed), workflow_id="does_not_exist", params={}
    )
    assert block["kind"] == "guide"


@pytest.mark.asyncio
async def test_no_approved_pack_blocks_generation(db_session, monkeypatch):
    seed = await _seed(db_session, with_pack=False)

    async def _fail_generate(db, **kwargs):  # must NOT be called
        raise AssertionError("generation must not run without an approved pack")

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _fail_generate
    )
    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="question_paper",
        params={"class_label": "8A", "subject": "Science"},
    )
    assert block["kind"] == "guide"
    assert "pack" in block["message"].lower()


@pytest.mark.asyncio
async def test_unauthorized_teacher_is_rejected(db_session, monkeypatch):
    """A teacher NOT mapped to teach this class+subject must be rejected by the EXISTING authz —
    JEV/Gemma selecting the workflow grants nothing."""
    from fastapi import HTTPException

    seed = await _seed(db_session, teacher_maps=False)

    async def _fake_generate(db, **kwargs):  # must NOT be reached
        raise AssertionError("unauthorized generation must not run")

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _fake_generate
    )
    with pytest.raises(HTTPException) as exc:
        await run_workflow(
            db_session, _user(seed),
            workflow_id="question_paper",
            params={"class_label": "8A", "subject": "Science"},
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_generation_failure_raises_workflow_error(db_session, monkeypatch):
    seed = await _seed(db_session)

    async def _boom(db, **kwargs):
        raise RuntimeError("llm down")

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _boom
    )
    monkeypatch.setattr(
        "app.modules.ai.services.usage_caps.enforce_monthly_ai_cap",
        lambda *a, **k: _acoro(1),
    )
    with pytest.raises(WorkflowError):
        await run_workflow(
            db_session, _user(seed),
            workflow_id="question_paper",
            params={"class_label": "8A", "subject": "Science"},
        )


def _acoro(value):
    async def _c():
        return value
    return _c()
