"""Phase 7: Parent Intervention — the FIRST governed state-changing action consumer.

Proves the full loop through the generic workflow model + a governed action:
  identify at-risk students -> resolve linked parents -> 1:1 drafts -> WAITING_FOR_APPROVAL ->
  authenticated Approve & Notify (server-side authz + re-validation + idempotency + audit) ->
  IN_APP notification -> COMPLETED.

Safety invariants asserted: nothing is sent during identify/draft; a model cannot approve; each
notification is strictly 1:1; duplicate approval is idempotent; failures are honest (never a
silent COMPLETED); every notification is audited.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser
from app.db.models.academic import AcademicYear, Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.audit import AuditLog
from app.db.models.notification import Notification
from app.db.models.parent_intervention import (
    INTERVENTION_STATUS_DRAFT,
    INTERVENTION_STATUS_NOTIFIED,
    ParentInterventionDraft,
)
from app.db.models.student import Parent, Student, StudentParentMap
from app.db.models.student import Relationship as ParentRel
from app.db.models.user import User, UserRole
from app.modules.workspace.workflows import (
    WorkflowState,
    get_workflow,
    list_workflows,
)
from app.modules.workspace.workflows.executor import run_workflow
from app.modules.workspace.workflows.parent_intervention_service import (
    InterventionError,
    ParentInterventionService,
)

# ── Registration ────────────────────────────────────────────────────────────


def test_parent_intervention_registered():
    wf = get_workflow("parent_intervention")
    assert wf is not None
    assert wf.approval_required is True
    assert wf.io.input_schema.__name__ == "ParentInterventionRequest"
    assert wf.io.output_schema.__name__ == "ParentInterventionOut"
    assert wf.domain_resource == "parent_intervention"


def test_four_workflows_share_one_registry():
    ids = {w.workflow_id for w in list_workflows()}
    assert {
        "question_paper", "evaluate_answer_sheet", "lesson_plan", "parent_intervention",
    } <= ids


# ── Seed ──────────────────────────────────────────────────────────────────────


async def _seed(db, *, low_attendance=True, with_parent=True):
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
    db.add_all([cls, admin])
    await db.flush()
    student_user = User(
        school_id=school.id, mobile=mob(), full_name="Asha",
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

    parent_user = None
    if with_parent:
        parent_user = User(
            school_id=school.id, mobile=mob(), full_name="Asha's Mother",
            role=UserRole.PARENT, is_active=True,
        )
        db.add(parent_user)
        await db.flush()
        parent = Parent(school_id=school.id, user_id=parent_user.id)
        db.add(parent)
        await db.flush()
        db.add(StudentParentMap(
            school_id=school.id, student_id=student.id, parent_id=parent.id,
            is_primary=True, relationship_type=ParentRel.MOTHER,
        ))
        await db.flush()

    # 10 days of attendance: mostly absent when low_attendance, else mostly present.
    for i in range(10):
        status = (
            AttendanceStatus.ABSENT if (low_attendance and i < 7) else AttendanceStatus.PRESENT
        )
        db.add(Attendance(
            school_id=school.id, student_id=student.id, class_id=cls.id,
            date=date(2026, 6, 1) + timedelta(days=i), status=status, marked_by=admin.id,
        ))
    await db.flush()
    return SimpleNamespace(
        school=school, cls=cls, admin=admin, student=student, parent_user=parent_user,
    )


def _mk_school():
    from app.db.models.school import School

    suffix = uuid.uuid4().hex[:8]
    return School(
        name="PI", code=f"PI{suffix}", tenant_slug=f"pi-{suffix}", board="SSC",
        contact_email=f"a-{suffix}@pi.com", contact_phone="+910000000209", is_active=True,
    )


def _mobile_gen():
    """Unique +91 mobiles per seeded school so two schools in one test don't collide."""
    base = 9000000000 + uuid.uuid4().int % 90000000

    def _next() -> str:
        nonlocal base
        base += 1
        return f"+91{base}"

    return _next


def _admin(seed) -> CurrentUser:
    return CurrentUser(
        id=str(seed.admin.id), school_id=str(seed.school.id), role="admin",
        tenant_slug="test", full_name="Principal", mobile="+910000000200",
        is_active=True, jti="j",
    )


# ── Workflow: identify + draft (SENDS NOTHING) ─────────────────────────────────


@pytest.mark.asyncio
async def test_workflow_drafts_but_sends_nothing(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _admin(seed), workflow_id="parent_intervention", params={}
    )
    assert block["kind"] == "workflow"
    assert block["workflow_state"] == WorkflowState.WAITING_FOR_APPROVAL.value
    assert len(block["drafts"]) == 1
    assert block["drafts"][0]["status"] == INTERVENTION_STATUS_DRAFT
    # Nothing sent during identification/drafting.
    count = await db_session.scalar(select(func.count()).select_from(Notification))
    assert count == 0


@pytest.mark.asyncio
async def test_workflow_1to1_targeting(db_session):
    seed = await _seed(db_session)
    block = await run_workflow(
        db_session, _admin(seed), workflow_id="parent_intervention", params={}
    )
    # One draft, targeted to the one linked parent — not a bulk notification.
    assert block["summary"]["total_students"] == 1
    assert block["summary"]["total_recipients"] == 1
    assert "Asha" in block["drafts"][0]["message"]


@pytest.mark.asyncio
async def test_no_at_risk_students_guides(db_session):
    seed = await _seed(db_session, low_attendance=False)
    block = await run_workflow(
        db_session, _admin(seed), workflow_id="parent_intervention", params={}
    )
    assert block["kind"] == "guide"


@pytest.mark.asyncio
async def test_missing_parent_mapping_excludes_student(db_session):
    seed = await _seed(db_session, with_parent=False)
    block = await run_workflow(
        db_session, _admin(seed), workflow_id="parent_intervention", params={}
    )
    # No linked parent -> no targetable recipient -> nothing to intervene on.
    assert block["kind"] == "guide"


# ── Action: approve & notify (governed) ────────────────────────────────────────


async def _make_draft(db, seed) -> ParentInterventionDraft:
    svc = ParentInterventionService(db)
    _, drafts = await svc.create_batch(
        school_id=seed.school.id, created_by=seed.admin.id, threshold=75.0
    )
    return drafts[0]


@pytest.mark.asyncio
async def test_approval_creates_one_in_app_notification(db_session):
    seed = await _seed(db_session)
    draft = await _make_draft(db_session, seed)
    svc = ParentInterventionService(db_session)
    result = await svc.approve_and_notify(_admin(seed), draft_id=draft.id)
    assert result.status == INTERVENTION_STATUS_NOTIFIED
    assert result.notification_id is not None
    notifs = (await db_session.execute(select(Notification))).scalars().all()
    assert len(notifs) == 1
    assert notifs[0].user_id == seed.parent_user.id       # 1:1 to the linked parent
    assert notifs[0].channel.value == "in_app"


@pytest.mark.asyncio
async def test_approval_is_idempotent(db_session):
    seed = await _seed(db_session)
    draft = await _make_draft(db_session, seed)
    svc = ParentInterventionService(db_session)
    first = await svc.approve_and_notify(_admin(seed), draft_id=draft.id)
    second = await svc.approve_and_notify(_admin(seed), draft_id=draft.id)  # duplicate
    assert first.notification_id == second.notification_id
    count = await db_session.scalar(select(func.count()).select_from(Notification))
    assert count == 1  # no duplicate notification


@pytest.mark.asyncio
async def test_approval_writes_audit(db_session):
    seed = await _seed(db_session)
    draft = await _make_draft(db_session, seed)
    svc = ParentInterventionService(db_session)
    await svc.approve_and_notify(_admin(seed), draft_id=draft.id)
    audits = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == "workflow.parent_intervention.notify"
            )
        )
    ).scalars().all()
    assert len(audits) == 1
    assert audits[0].resource_id == str(draft.id)
    assert audits[0].details["notification_id"]
    assert audits[0].user_id == seed.admin.id


@pytest.mark.asyncio
async def test_unauthorized_approver_rejected(db_session):
    """A plain teacher with no scope over the student cannot approve (re-validated at approve)."""
    from fastapi import HTTPException

    seed = await _seed(db_session)
    draft = await _make_draft(db_session, seed)
    outsider = User(
        school_id=seed.school.id, mobile="+910000000288", full_name="Outsider",
        role=UserRole.TEACHER, is_active=True,
    )
    db_session.add(outsider)
    await db_session.flush()
    user = CurrentUser(
        id=str(outsider.id), school_id=str(seed.school.id), role="teacher",
        tenant_slug="test", full_name="Outsider", mobile="+910000000288",
        is_active=True, jti="j",
    )
    svc = ParentInterventionService(db_session)
    with pytest.raises(HTTPException) as exc:
        await svc.approve_and_notify(user, draft_id=draft.id)
    assert exc.value.status_code == 403
    # Nothing sent on a rejected approval.
    count = await db_session.scalar(select(func.count()).select_from(Notification))
    assert count == 0


@pytest.mark.asyncio
async def test_tenant_isolation_on_approval(db_session):
    """A draft from school A cannot be approved by a user from school B."""
    seed_a = await _seed(db_session)
    draft = await _make_draft(db_session, seed_a)
    seed_b = await _seed(db_session)  # separate school
    svc = ParentInterventionService(db_session)
    with pytest.raises(InterventionError):
        await svc.approve_and_notify(_admin(seed_b), draft_id=draft.id)


@pytest.mark.asyncio
async def test_notification_failure_is_honest(db_session, monkeypatch):
    seed = await _seed(db_session)
    draft = await _make_draft(db_session, seed)

    async def _boom(self, *a, **k):
        raise RuntimeError("notify down")

    monkeypatch.setattr(
        "app.modules.notifications.services.notification_service.NotificationService.send",
        _boom,
    )
    svc = ParentInterventionService(db_session)
    with pytest.raises(InterventionError):
        await svc.approve_and_notify(_admin(seed), draft_id=draft.id)
    # Domain state reflects failure honestly — never a silent notified/COMPLETED.
    refreshed = await db_session.get(ParentInterventionDraft, draft.id)
    assert refreshed.status != INTERVENTION_STATUS_NOTIFIED
    assert refreshed.notification_id is None
