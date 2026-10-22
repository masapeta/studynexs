"""Phase 10B: Question Paper generation runs asynchronously on the existing Arq worker.

Production QP generation no longer blocks the request: the executor enqueues a job and returns a
QUEUED workflow block the chat polls; the worker runs the UNCHANGED `generate_paper` pipeline.
These tests force the non-TESTING branch (TESTING still runs synchronously — covered by
test_question_paper_workflow.py) and assert the orchestration: enqueue, idempotency, graceful
sync fallback, job-handler execution, and that the QP domain lifecycle + authorization are intact.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

# Import the worker + job modules now, with REAL settings, so their module-level initialisation
# (queue.py caches settings; worker.py builds RedisSettings) is never evaluated under the fake
# production settings a test installs below.
import app.core.jobs.queue  # noqa: E402
import app.core.jobs.worker  # noqa: E402,F401
from app.core.config import Environment
from app.core.dependencies import CurrentUser
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.curriculum_pack import CurriculumPack, PackStatus
from app.db.models.job import Job, JobStatus
from app.db.models.question_paper import PaperStatus
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.jobs.question_paper_job import (  # noqa: E402
    run_question_paper_generate,
)
from app.modules.workspace.workflows.executor import run_workflow


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
        db.add(TeacherSubjectMapping(
            school_id=school.id, teacher_id=teacher.id,
            class_id=cls.id, subject_id=subject.id,
        ))
        await db.flush()
    if with_pack:
        db.add(CurriculumPack(
            school_id=school.id, class_id=cls.id, subject_id=subject.id,
            academic_year_id=ay.id, board="SSC", version=1, created_by=teacher.id,
            status=PackStatus.APPROVED,
        ))
        await db.flush()
    return SimpleNamespace(school=school, cls=cls, subject=subject, teacher=teacher)


def _user(seed) -> CurrentUser:
    return CurrentUser(
        id=str(seed.teacher.id), school_id=str(seed.school.id), role="teacher",
        tenant_slug="test", full_name="T", mobile="+910000000001",
        is_active=True, jti="j",
    )


def _acoro(value):
    async def _c():
        return value
    return _c()


def _force_production(monkeypatch):
    """Make the executor take the async (non-TESTING) branch without touching the real env."""
    fake = SimpleNamespace(ENVIRONMENT=Environment.PRODUCTION)
    monkeypatch.setattr("app.core.config.get_settings", lambda: fake)
    monkeypatch.setattr(
        "app.modules.ai.services.usage_caps.enforce_monthly_ai_cap",
        lambda *a, **k: _acoro(1),
    )


# ── Enqueue path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_production_enqueues_and_returns_queued_block(db_session, monkeypatch):
    seed = await _seed(db_session)
    _force_production(monkeypatch)
    enqueued = {}

    async def _fake_enqueue(db, *, task, params, school_id, created_by):
        enqueued.update(task=task, params=params, school_id=school_id, created_by=created_by)
        job = Job(type=task, params=params, school_id=school_id,
                  created_by=created_by, status=JobStatus.QUEUED)
        db.add(job)
        await db.flush()
        return job

    # Generation must NOT run inline on the request path.
    async def _must_not_generate(db, **kwargs):
        raise AssertionError("generate_paper must not run inline in production")

    monkeypatch.setattr("app.core.jobs.queue.enqueue", _fake_enqueue)
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _must_not_generate
    )

    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="question_paper",
        params={"class_label": "8A", "subject": "Science", "total_marks": 50},
    )
    assert block["kind"] == "workflow"
    assert block["workflow_id"] == "question_paper"
    assert block["workflow_state"] == "queued"
    assert uuid.UUID(block["summary"]["job_id"])  # pollable reference
    assert "paper_id" not in block["summary"]  # no paper exists yet — we don't imply one
    assert enqueued["task"] == "question_paper_generate"
    assert enqueued["params"]["class_id"] == str(seed.cls.id)
    assert enqueued["params"]["pack_id"] is not None
    assert enqueued["school_id"] == seed.school.id


@pytest.mark.asyncio
async def test_duplicate_submission_reuses_inflight_job(db_session, monkeypatch):
    seed = await _seed(db_session)
    _force_production(monkeypatch)

    calls = {"n": 0}

    async def _fake_enqueue(db, *, task, params, school_id, created_by):
        calls["n"] += 1
        job = Job(type=task, params=params, school_id=school_id,
                  created_by=created_by, status=JobStatus.QUEUED)
        db.add(job)
        await db.flush()
        return job

    monkeypatch.setattr("app.core.jobs.queue.enqueue", _fake_enqueue)

    params = {"class_label": "8A", "subject": "Science", "total_marks": 50}
    first = await run_workflow(
        db_session, _user(seed), workflow_id="question_paper", params=params
    )
    second = await run_workflow(
        db_session, _user(seed), workflow_id="question_paper", params=params
    )
    # The in-flight job is reused — no second enqueue, no second generation/charge.
    assert calls["n"] == 1
    assert first["summary"]["job_id"] == second["summary"]["job_id"]
    assert second["workflow_state"] == "queued"


@pytest.mark.asyncio
async def test_enqueue_failure_falls_back_to_sync(db_session, monkeypatch):
    seed = await _seed(db_session)
    _force_production(monkeypatch)

    async def _broken_enqueue(db, **kwargs):
        raise RuntimeError("redis down")

    async def _fake_generate(db, **kwargs):
        return SimpleNamespace(
            id=uuid.uuid4(), total_marks=Decimal("50"), status=PaperStatus.DRAFT,
            grounded=True, sections=[SimpleNamespace(questions=[object(), object()])],
        )

    monkeypatch.setattr("app.core.jobs.queue.enqueue", _broken_enqueue)
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _fake_generate
    )

    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="question_paper",
        params={"class_label": "8A", "subject": "Science", "total_marks": 50},
    )
    # Graceful degradation: a Redis/worker outage still produces a paper synchronously.
    assert block["kind"] == "workflow"
    assert block["workflow_state"] == "waiting_for_approval"
    assert block["paper_status"] == "draft"


@pytest.mark.asyncio
async def test_unauthorized_teacher_rejected_before_enqueue(db_session, monkeypatch):
    """Authorization still runs up front — the planner selecting the workflow grants nothing."""
    from fastapi import HTTPException

    seed = await _seed(db_session, teacher_maps=False)
    _force_production(monkeypatch)

    async def _must_not_enqueue(db, **kwargs):
        raise AssertionError("must not enqueue for an unauthorized teacher")

    monkeypatch.setattr("app.core.jobs.queue.enqueue", _must_not_enqueue)
    with pytest.raises(HTTPException) as exc:
        await run_workflow(
            db_session, _user(seed),
            workflow_id="question_paper",
            params={"class_label": "8A", "subject": "Science"},
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_no_pack_blocks_before_enqueue(db_session, monkeypatch):
    seed = await _seed(db_session, with_pack=False)
    _force_production(monkeypatch)

    async def _must_not_enqueue(db, **kwargs):
        raise AssertionError("must not enqueue without an approved pack")

    monkeypatch.setattr("app.core.jobs.queue.enqueue", _must_not_enqueue)
    block = await run_workflow(
        db_session, _user(seed),
        workflow_id="question_paper",
        params={"class_label": "8A", "subject": "Science"},
    )
    assert block["kind"] == "guide"
    assert "pack" in block["message"].lower()


# ── Job handler ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_job_handler_runs_generation(db_session, monkeypatch):
    seed = await _seed(db_session)
    paper_id = uuid.uuid4()

    async def _fake_generate(db, **kwargs):
        return SimpleNamespace(id=paper_id, status=PaperStatus.DRAFT)

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_paper", _fake_generate
    )
    out = await run_question_paper_generate(
        {
            "school_id": str(seed.school.id),
            "created_by": str(seed.teacher.id),
            "class_id": str(seed.cls.id),
            "subject_id": str(seed.subject.id),
            "topics": [],
            "total_marks": 50,
            "role": "teacher",
            "purpose_tag": "qp_full",
            "credits_charged": 1,
            "pack_id": None,
        },
        db_session,
    )
    assert out["paper_id"] == str(paper_id)
    assert out["paper_status"] == "draft"
