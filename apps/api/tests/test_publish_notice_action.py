"""Phase 8: Publish Notice — the SECOND governed assistant ACTION (after parent-intervention).

Proves the governance pattern generalizes to a materially different action: a stateless
create-on-confirm (no persisted draft), idempotent via a server-issued action token.

  interpret -> preview (validate + authorize + mint token, creates nothing) ->
  WAITING_FOR_CONFIRMATION -> authenticated confirm -> re-authorize + validate + idempotent ->
  NoticeService.create_notice -> audit -> completed.

A model can never confirm; identical content may legitimately be republished with a fresh token;
a retried token never duplicates the notice.
"""

from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser
from app.db.models.academic import AcademicYear, Class
from app.db.models.audit import AuditLog
from app.db.models.communication import Notice
from app.db.models.governed_action import GovernedActionExecution
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.workspace.workflows.notice_action_service import (
    NoticeActionError,
    NoticeActionService,
)


def _mk_school():
    suffix = uuid.uuid4().hex[:8]
    return School(
        name="PN", code=f"PN{suffix}", tenant_slug=f"pn-{suffix}", board="SSC",
        contact_email=f"a-{suffix}@pn.com", contact_phone="+910000000309", is_active=True,
    )


def _mobile_gen():
    base = 9000000000 + uuid.uuid4().int % 90000000

    def _next() -> str:
        nonlocal base
        base += 1
        return f"+91{base}"

    return _next


async def _seed(db):
    school = _mk_school()
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    mob = _mobile_gen()
    cls = Class(school_id=school.id, grade="8", section="A", academic_year_id=ay.id)
    admin = User(
        school_id=school.id, mobile=mob(), full_name="Principal",
        role=UserRole.ADMIN, is_active=True,
    )
    teacher = User(
        school_id=school.id, mobile=mob(), full_name="Teacher",
        role=UserRole.TEACHER, is_active=True,
    )
    db.add_all([cls, admin, teacher])
    await db.flush()
    return SimpleNamespace(school=school, cls=cls, admin=admin, teacher=teacher)


def _user(u, school, role) -> CurrentUser:
    return CurrentUser(
        id=str(u.id), school_id=str(school.id), role=role, tenant_slug="test",
        full_name=u.full_name, mobile=u.mobile, is_active=True, jti="j",
    )


# ── Planner routing ────────────────────────────────────────────────────────────


def test_planner_decision_models_publish_notice_action():
    from app.modules.workspace.assistant.planner import PlannerDecision

    d = PlannerDecision(
        action="act", route="ACTION", action_target="publish_notice",
        params={"title": "Holiday", "content": "Tomorrow is a holiday", "audience": "external"},
    )
    assert d.action == "act"
    assert d.action_target == "publish_notice"
    assert d.tool is None and d.workflow_id is None  # action is neither capability nor workflow


# ── Preview (creates nothing) ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_preview_validates_and_mints_token_without_creating(db_session):
    seed = await _seed(db_session)
    svc = NoticeActionService(db_session)
    preview = await svc.preview(
        _user(seed.admin, seed.school, "admin"),
        title="Holiday", content="Tomorrow is a holiday", audience="external",
        class_label="8A",
    )
    assert preview.action_token is not None
    assert preview.class_id == seed.cls.id
    # Nothing created during preview.
    assert await db_session.scalar(select(func.count()).select_from(Notice)) == 0
    assert await db_session.scalar(
        select(func.count()).select_from(GovernedActionExecution)
    ) == 0


@pytest.mark.asyncio
async def test_preview_requires_title_and_content(db_session):
    seed = await _seed(db_session)
    svc = NoticeActionService(db_session)
    with pytest.raises(NoticeActionError):
        await svc.preview(
            _user(seed.admin, seed.school, "admin"),
            title="", content="", audience="external",
        )


@pytest.mark.asyncio
async def test_preview_rejects_unknown_audience(db_session):
    seed = await _seed(db_session)
    svc = NoticeActionService(db_session)
    with pytest.raises(NoticeActionError):
        await svc.preview(
            _user(seed.admin, seed.school, "admin"),
            title="T", content="C", audience="carrier-pigeon",
        )


@pytest.mark.asyncio
async def test_preview_internal_notice_rejected_for_teacher(db_session):
    """Internal (staff) notices are admin-only — authorized at preview time."""
    from fastapi import HTTPException

    seed = await _seed(db_session)
    svc = NoticeActionService(db_session)
    with pytest.raises(HTTPException) as exc:
        await svc.preview(
            _user(seed.teacher, seed.school, "teacher"),
            title="Staff meeting", content="At 4pm", audience="internal",
        )
    assert exc.value.status_code == 403


# ── Confirm (the governed state change) ────────────────────────────────────────


async def _preview(db, seed):
    return await NoticeActionService(db).preview(
        _user(seed.admin, seed.school, "admin"),
        title="Holiday", content="Tomorrow is a holiday", audience="external",
        class_label="8A",
    )


@pytest.mark.asyncio
async def test_confirm_publishes_notice_and_audits(db_session):
    seed = await _seed(db_session)
    p = await _preview(db_session, seed)
    svc = NoticeActionService(db_session)
    notice, created = await svc.confirm_publish(
        _user(seed.admin, seed.school, "admin"),
        action_token=p.action_token, title=p.title, content=p.content,
        audience=p.audience, class_id=p.class_id, target_roles=p.target_roles,
        priority=p.priority,
    )
    assert created is True
    assert notice.id is not None
    # Notice actually created via NoticeService.
    assert await db_session.scalar(select(func.count()).select_from(Notice)) == 1
    # Audit written.
    audits = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.action == "action.publish_notice")
        )
    ).scalars().all()
    assert len(audits) == 1
    assert audits[0].resource_id == str(notice.id)


@pytest.mark.asyncio
async def test_confirm_is_idempotent_on_token(db_session):
    seed = await _seed(db_session)
    p = await _preview(db_session, seed)
    svc = NoticeActionService(db_session)
    kwargs = dict(
        action_token=p.action_token, title=p.title, content=p.content,
        audience=p.audience, class_id=p.class_id, target_roles=p.target_roles,
        priority=p.priority,
    )
    n1, c1 = await svc.confirm_publish(_user(seed.admin, seed.school, "admin"), **kwargs)
    n2, c2 = await svc.confirm_publish(_user(seed.admin, seed.school, "admin"), **kwargs)
    assert c1 is True and c2 is False      # second is idempotent replay
    assert n1.id == n2.id
    assert await db_session.scalar(select(func.count()).select_from(Notice)) == 1


@pytest.mark.asyncio
async def test_identical_content_republishes_with_fresh_token(db_session):
    """A school may legitimately publish identical content twice — a NEW token is a NEW notice."""
    seed = await _seed(db_session)
    svc = NoticeActionService(db_session)
    p1 = await _preview(db_session, seed)
    await svc.confirm_publish(
        _user(seed.admin, seed.school, "admin"),
        action_token=p1.action_token, title=p1.title, content=p1.content,
        audience=p1.audience, class_id=p1.class_id, target_roles=p1.target_roles,
        priority=p1.priority,
    )
    p2 = await _preview(db_session, seed)  # fresh token, same content
    _, created = await svc.confirm_publish(
        _user(seed.admin, seed.school, "admin"),
        action_token=p2.action_token, title=p2.title, content=p2.content,
        audience=p2.audience, class_id=p2.class_id, target_roles=p2.target_roles,
        priority=p2.priority,
    )
    assert created is True
    assert await db_session.scalar(select(func.count()).select_from(Notice)) == 2


@pytest.mark.asyncio
async def test_confirm_reauthorizes_at_execution_time(db_session):
    """A plain teacher cannot publish an external school-wide notice even with a valid token."""
    from fastapi import HTTPException

    seed = await _seed(db_session)
    # Admin previews (authorized), but a teacher attempts the confirm.
    p = await NoticeActionService(db_session).preview(
        _user(seed.admin, seed.school, "admin"),
        title="Holiday", content="Tomorrow is a holiday", audience="external",
    )
    svc = NoticeActionService(db_session)
    with pytest.raises(HTTPException) as exc:
        await svc.confirm_publish(
            _user(seed.teacher, seed.school, "teacher"),
            action_token=p.action_token, title=p.title, content=p.content,
            audience=p.audience, class_id=p.class_id, target_roles=p.target_roles,
            priority=p.priority,
        )
    assert exc.value.status_code == 403
    assert await db_session.scalar(select(func.count()).select_from(Notice)) == 0
