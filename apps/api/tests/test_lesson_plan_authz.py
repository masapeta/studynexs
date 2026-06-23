"""Unit tests for lesson-plan edit/approve authorization (segregation of duties + scope)."""
from __future__ import annotations

import uuid

from app.core.staff_permissions import StaffScope
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService

SVC = LessonPlanService(db=None)  # can_edit/can_approve don't touch the session


def _plan(
    class_id: uuid.UUID, subject_id: uuid.UUID, creator: uuid.UUID,
    status: LessonPlanStatus = LessonPlanStatus.DRAFT,
) -> LessonPlan:
    return LessonPlan(
        school_id=uuid.uuid4(),
        class_id=class_id,
        subject_id=subject_id,
        created_by=creator,
        title="Plan",
        topic="Algebra",
        segments=[],
        status=status,
    )


def _scope(user_id, *, is_admin=False, incharge=None, teaching=None) -> StaffScope:
    return StaffScope(
        user_id=user_id,
        role="admin" if is_admin else "teacher",
        is_admin=is_admin,
        incharge_class_ids=set(incharge or []),
        teaching_pairs=set(teaching or []),
    )


# ── approval: segregation of duties ──────────────────────────────────────────

def test_subject_teacher_cannot_approve_own_lesson_plan():
    cid, sid, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, tid)
    scope = _scope(tid, teaching={(cid, sid)})  # author + teaches it, but not incharge
    assert SVC.can_approve(scope, plan) is False


def test_class_incharge_can_approve_lesson_plan():
    cid, sid, author, incharge = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, author)
    scope = _scope(incharge, incharge=[cid])
    assert SVC.can_approve(scope, plan) is True


def test_admin_can_approve_lesson_plan():
    cid, sid = uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, uuid.uuid4())
    assert SVC.can_approve(_scope(uuid.uuid4(), is_admin=True), plan) is True


def test_approved_plan_cannot_be_reapproved():
    cid, sid = uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, uuid.uuid4(), status=LessonPlanStatus.APPROVED)
    assert SVC.can_approve(_scope(uuid.uuid4(), is_admin=True), plan) is False


# ── edit: no stale authorization ─────────────────────────────────────────────

def test_author_can_edit_own_draft_while_assigned():
    cid, sid, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, tid)
    scope = _scope(tid, teaching={(cid, sid)})
    assert SVC.can_edit(scope, plan) is True


def test_author_cannot_edit_after_losing_assignment():
    cid, sid, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, tid)
    scope = _scope(tid, teaching=set())  # pulled off the class/subject, not incharge
    assert SVC.can_edit(scope, plan) is False


def test_non_author_cannot_edit():
    cid, sid = uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, uuid.uuid4())
    other = _scope(uuid.uuid4(), teaching={(cid, sid)})
    assert SVC.can_edit(other, plan) is False


def test_cannot_edit_approved_plan():
    cid, sid, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plan = _plan(cid, sid, tid, status=LessonPlanStatus.APPROVED)
    scope = _scope(tid, teaching={(cid, sid)})
    assert SVC.can_edit(scope, plan) is False
