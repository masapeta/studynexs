"""Stage 2: result versions + governed release lifecycle (plan Rev 2 §3, §13.1 items 1–11).

Covers: every mark write versions (manual + AI approval), partial release with acknowledgement,
stale preview 409, token replay/actor binding/expiry/tamper, no_changes, late approval → gen 2,
reopen + changed marks → v2 hidden until gen 3, withdraw (admin) / incharge 403, block/unblock
preserving prior state (P12), admin cannot normally release (P-R1), notifications deduped per
generation (P-R7), historical baselines lazily (P-R2), learner APIs show only published versions,
mastery learner ledger gated, misconception provenance gating, composite tenant FKs.
"""
from __future__ import annotations

import time
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.audit import AuditLog
from app.db.models.exam_result import (
    ExamResultNotification,
    ExamResultPublished,
    ExamResultRelease,
    ExamResultVersion,
)
from app.db.models.examination import ExamMark
from app.db.models.mastery import AUDIENCE_LEARNER, AUDIENCE_STAFF, StudentTopicMastery
from app.db.models.misconception import MisconceptionEntry
from app.db.models.notification import Notification
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole
from app.modules.examinations.services.release_service import (
    ReleaseError,
    issue_preview_token,
    verify_preview_token,
)
from app.modules.mastery.services.audience import published_misconceptions_for_student
from app.modules.mastery.services.mastery_service import recompute_class_subject
from tests.conftest import access_token_for, auth_headers
from tests.test_answer_sheet_eval import _seed_eval_fixture

ANSWERS_GOOD = {"1": "4", "2": "B", "3": "Process by which plants make food using sunlight."}
ANSWERS_WEAK = {"1": "5", "2": "A", "3": "no idea"}


@pytest.fixture(autouse=True)
def _deterministic_grading(monkeypatch):
    """No network: subjective grading falls back to the deterministic heuristic."""

    async def _offline(*_a, **_k):
        raise RuntimeError("LLM disabled in tests")

    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service.evaluate_subjective",
        _offline,
    )


async def _user(db, school, role, name, mobile):
    u = User(
        school_id=school.id, username=name, mobile=mobile, full_name=name.title(),
        role=role, password_hash=hash_password("Pw@12345678"), is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


async def _world(db: AsyncSession):
    fx = await _seed_eval_fixture(db)
    school, cls = fx["school"], fx["class"]
    principal = await _user(db, school, UserRole.SUPER_ADMIN, "principal", "+910000000201")
    admin = await _user(db, school, UserRole.ADMIN, "admin1", "+910000000202")
    teacher = await _user(db, school, UserRole.TEACHER, "subj_t", "+910000000203")
    from app.db.models.academic import TeacherSubjectMapping

    db.add(TeacherSubjectMapping(
        school_id=school.id, teacher_id=teacher.id, class_id=cls.id, subject_id=fx["subject"].id,
    ))
    s2_user = await _user(db, school, UserRole.STUDENT, "stu2", "+910000000204")
    s2 = Student(school_id=school.id, user_id=s2_user.id, class_id=cls.id, roll_no="2",
                 admission_no="ADM2")
    db.add(s2)
    p_user = await _user(db, school, UserRole.PARENT, "parent1", "+910000000205")
    parent = Parent(school_id=school.id, user_id=p_user.id)
    db.add(parent)
    await db.flush()
    db.add(StudentParentMap(school_id=school.id, student_id=fx["student"].id, parent_id=parent.id,
                            is_primary=True, relationship_type=Relationship.FATHER))
    await db.flush()
    fx.update(principal=principal, admin=admin, teacher=teacher, student2=s2,
              student2_user=s2_user, parent_user=p_user)
    fx["student_user"] = await db.get(User, fx["student"].user_id)
    return fx


def _h(user) -> dict:
    return auth_headers(access_token_for(user))


async def _evaluate_and_approve(client, fx, student, answers, actor, overrides=None):
    r = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations", headers=_h(actor),
        json={"student_id": str(student.id), "student_answers": answers},
    )
    assert r.status_code == 201, r.text
    eid = r.json()["data"]["id"]
    r = await client.post(
        f"/api/v1/exams/evaluations/{eid}/approve", headers=_h(actor),
        json={"teacher_overrides": overrides or {}, "correction_summary": "Approved by teacher"},
    )
    assert r.status_code == 200, r.text
    return eid


async def _preview(client, fx, actor):
    return await client.post(f"/api/v1/exams/{fx['exam'].id}/release/preview", headers=_h(actor))


async def _confirm(client, fx, actor, p, **kw):
    body = {"preview_token": p["preview_token"], **kw}
    return await client.post(
        f"/api/v1/exams/{fx['exam'].id}/release/confirm", headers=_h(actor), json=body
    )


async def _versions(db, fx, student):
    return (await db.execute(
        select(ExamResultVersion).where(
            ExamResultVersion.exam_id == fx["exam"].id,
            ExamResultVersion.student_id == student.id,
        ).order_by(ExamResultVersion.version_no)
    )).scalars().all()


@pytest.mark.asyncio
async def test_full_release_lifecycle(client: AsyncClient, db_session: AsyncSession):
    fx = await _world(db_session)
    exam, s1, s2 = fx["exam"], fx["student"], fx["student2"]
    teacher, incharge, admin, principal = fx["teacher"], fx["incharge"], fx["admin"], fx["principal"]

    # 1. Pure subject teacher evaluates + approves → version v1 with AI provenance + revision.
    await _evaluate_and_approve(client, fx, s1, ANSWERS_WEAK, teacher)
    v = await _versions(db_session, fx, s1)
    assert [x.version_no for x in v] == [1]
    assert v[0].source == "ai_evaluation" and v[0].evaluation_revision_id is not None
    # Subject teacher still has no roster API, but sees submissions for the exam.
    assert (await client.get(f"/api/v1/academic/students?class_id={fx['class'].id}",
                             headers=_h(teacher))).status_code == 403
    subs = await client.get(f"/api/v1/exams/{exam.id}/submissions", headers=_h(teacher))
    assert subs.status_code == 200
    assert {r["status"] for r in subs.json()["data"]} == {"approved", "not_submitted"}

    # 2. Before release: learner sees "pending", nothing else.
    r = await client.get("/api/v1/portal/results", headers=_h(fx["student_user"]))
    assert r.status_code == 200
    mine = [x for x in r.json()["data"] if x["exam_id"] == str(exam.id)][0]
    assert mine["status"] == "pending" and mine["marks_obtained"] is None
    await recompute_class_subject(db_session, fx["school"].id, fx["class"].id, fx["subject"].id)
    learner_rows = (await db_session.execute(select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == s1.id,
        StudentTopicMastery.audience == AUDIENCE_LEARNER))).scalars().all()
    staff_rows = (await db_session.execute(select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == s1.id,
        StudentTopicMastery.audience == AUDIENCE_STAFF))).scalars().all()
    assert learner_rows == [] and staff_rows  # staff sees it before release; learners don't
    mp = await client.get(f"/api/v1/mastery/students/{s1.id}", headers=_h(fx["student_user"]))
    assert mp.json()["data"]["subjects"] == []

    # Authority: subject teacher + admin cannot release (P-R1); preview is 403.
    assert (await _preview(client, fx, teacher)).status_code == 403
    assert (await _preview(client, fx, admin)).status_code == 403

    # 3. Partial release by incharge: s2 still pending.
    p = (await _preview(client, fx, incharge)).json()["data"]
    assert p["pending_total"] == 1 and p["eligible_count"] == 1
    r = await _confirm(client, fx, incharge, p)
    assert r.status_code == 400 and r.json()["code"] == "partial_not_confirmed"
    r = await _confirm(client, fx, incharge, p, confirm_partial=True, acknowledged_pending_count=0)
    assert r.status_code == 400 and r.json()["code"] == "pending_count_mismatch"
    r = await _confirm(client, fx, incharge, p, confirm_partial=True, acknowledged_pending_count=1)
    assert r.status_code == 200, r.text
    gen1 = r.json()["data"]["release"]
    assert gen1["generation_no"] == 1 and gen1["partial"] is True

    # 5. Replay of the same token → same generation, nothing new.
    r = await _confirm(client, fx, incharge, p, confirm_partial=True, acknowledged_pending_count=1)
    assert r.status_code == 200 and r.json()["data"]["replayed"] is True
    assert r.json()["data"]["release"]["id"] == gen1["id"]
    released_audits = await db_session.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action == "result.released", AuditLog.resource_id == str(exam.id)))
    assert released_audits == 1

    # Learner sees v1; s2 pending; notifications: student + parent once.
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["status"] == "released"
    v1_marks = r.json()["data"]["marks_obtained"]
    r = await client.get(f"/api/v1/portal/child/{s1.id}/results/{exam.id}",
                         headers=_h(fx["parent_user"]))
    assert r.json()["data"]["marks_obtained"] == v1_marks
    n1 = await db_session.scalar(select(func.count()).select_from(ExamResultNotification))
    assert n1 == 2
    # Released → learner ledger now populated.
    await recompute_class_subject(db_session, fx["school"].id, fx["class"].id, fx["subject"].id)
    assert (await db_session.execute(select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == s1.id,
        StudentTopicMastery.audience == AUDIENCE_LEARNER))).scalars().all()

    # New preview with nothing new → no_changes, no generation.
    p2 = (await _preview(client, fx, incharge)).json()["data"]
    r = await _confirm(client, fx, incharge, p2, confirm_partial=True,
                       acknowledged_pending_count=p2["pending_total"])
    assert r.json()["data"]["no_changes"] is True

    # 4. Stale preview: preview, then another approval lands, then confirm → 409.
    p3 = (await _preview(client, fx, incharge)).json()["data"]
    await _evaluate_and_approve(client, fx, s2, ANSWERS_GOOD, teacher)
    r = await _confirm(client, fx, incharge, p3, confirm_partial=True, acknowledged_pending_count=1)
    assert r.status_code == 409 and r.json()["code"] == "stale_preview"
    assert await db_session.scalar(select(func.count()).select_from(ExamResultRelease).where(
        ExamResultRelease.action == "release")) == 1

    # 6. Late approval → re-release gen 2 publishes only s2; s1 unaffected.
    p4 = (await _preview(client, fx, incharge)).json()["data"]
    assert p4["pending_total"] == 0 and p4["changes_count"] == 1
    r = await _confirm(client, fx, incharge, p4)
    assert r.json()["data"]["release"]["generation_no"] == 2
    assert await db_session.scalar(select(func.count()).select_from(ExamResultNotification)) == 3

    # 7. Reopen s1 (incharge) → re-approve with changed marks → v2; student still sees v1.
    ev1 = (await db_session.execute(select(ExamMark).where(
        ExamMark.exam_id == exam.id, ExamMark.student_id == s1.id))).scalar_one()
    eid1 = ev1.source_evaluation_id
    assert (await client.post(f"/api/v1/exams/evaluations/{eid1}/reopen", headers=_h(teacher),
                              json={"reason": "recheck"})).status_code == 403
    r = await client.post(f"/api/v1/exams/evaluations/{eid1}/reopen", headers=_h(incharge),
                          json={"reason": "Recheck Q3"})
    assert r.status_code == 200, r.text
    r = await client.post(f"/api/v1/exams/evaluations/{eid1}/approve", headers=_h(incharge),
                          json={"teacher_overrides": {"3": {"marks": 2, "reason": "partial"}}})
    assert r.status_code == 200, r.text
    vs = await _versions(db_session, fx, s1)
    assert [x.version_no for x in vs] == [1, 2]
    assert float(vs[1].marks_obtained) != float(vs[0].marks_obtained), (
        vs[0].question_marks, vs[1].question_marks)
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["marks_obtained"] == v1_marks
    subs = (await client.get(f"/api/v1/exams/{exam.id}/submissions",
                             headers=_h(incharge))).json()["data"]
    assert [x for x in subs if x["student_id"] == str(s1.id)][0]["changed_since_release"] is True
    revs = await client.get(f"/api/v1/exams/evaluations/{eid1}/revisions", headers=_h(teacher))
    assert [x["kind"] for x in revs.json()["data"]] == ["approved", "reopened", "approved"]
    p5 = (await _preview(client, fx, incharge)).json()["data"]
    r = await _confirm(client, fx, incharge, p5)
    assert r.json()["data"]["release"]["generation_no"] == 3
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["marks_obtained"] != v1_marks

    # 9. Block/unblock (P12): admin cannot block; principal blocks → hidden; incharge blocked.
    tok = str(uuid.uuid4())
    r = await client.post(f"/api/v1/exams/{exam.id}/release/block", headers=_h(admin),
                          json={"reason": "check", "action_token": tok})
    assert r.status_code == 403
    r = await client.post(f"/api/v1/exams/{exam.id}/release/block", headers=_h(principal),
                          json={"reason": "Complaint review", "action_token": tok})
    assert r.status_code == 200 and r.json()["data"]["prior_status"] == "released"
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["status"] == "pending"
    r = await _preview(client, fx, incharge)
    assert r.status_code == 409 and r.json()["code"] == "blocked"
    r = await client.post(f"/api/v1/exams/{exam.id}/release/unblock", headers=_h(principal),
                          json={"reason": "Resolved", "action_token": str(uuid.uuid4())})
    assert r.status_code == 200 and r.json()["data"]["resulting_status"] == "released"
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["status"] == "released"  # prior condition restored exactly

    # 8. Withdraw: incharge 403; admin withdraws → learner views clear.
    wt = str(uuid.uuid4())
    r = await client.post(f"/api/v1/exams/{exam.id}/release/withdraw", headers=_h(incharge),
                          json={"reason": "x", "action_token": wt})
    assert r.status_code == 403
    r = await client.post(f"/api/v1/exams/{exam.id}/release/withdraw", headers=_h(admin),
                          json={"reason": "Marks error", "action_token": wt})
    assert r.status_code == 200
    assert await db_session.scalar(select(func.count()).select_from(ExamResultPublished)) == 0
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["status"] == "pending"
    await recompute_class_subject(db_session, fx["school"].id, fx["class"].id, fx["subject"].id)
    assert (await db_session.execute(select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == s1.id,
        StudentTopicMastery.audience == AUDIENCE_LEARNER))).scalars().all() == []

    # Block while withdrawn → unblock restores 'withdrawn' (never exposes withdrawn results).
    await client.post(f"/api/v1/exams/{exam.id}/release/block", headers=_h(principal),
                      json={"reason": "Hold", "action_token": str(uuid.uuid4())})
    r = await client.post(f"/api/v1/exams/{exam.id}/release/unblock", headers=_h(principal),
                          json={"reason": "Done", "action_token": str(uuid.uuid4())})
    assert r.json()["data"]["resulting_status"] == "withdrawn"
    r = await client.get(f"/api/v1/portal/results/{exam.id}", headers=_h(fx["student_user"]))
    assert r.json()["data"]["status"] == "pending"

    # Re-release after withdraw: principal releases all eligible → gen 4, "Updated results".
    p6 = (await _preview(client, fx, principal)).json()["data"]
    assert p6["changes_count"] == 2
    r = await _confirm(client, fx, principal, p6)
    assert r.json()["data"]["release"]["generation_no"] == 4
    titles = (await db_session.execute(select(Notification.title).where(
        Notification.user_id == fx["parent_user"].id))).scalars().all()
    assert sum("Updated results" in t for t in titles) >= 1


@pytest.mark.asyncio
async def test_manual_marks_create_versions_and_noop_resave(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    body = {"exam_id": str(fx["exam"].id), "entries": [
        {"student_id": str(fx["student"].id), "marks_obtained": 4}]}
    for _ in range(2):
        assert (await client.post("/api/v1/exams/marks", headers=_h(fx["incharge"]),
                                  json=body)).status_code == 200
    v = await _versions(db_session, fx, fx["student"])
    assert [x.version_no for x in v] == [1] and v[0].source == "manual_entry"
    body["entries"][0]["marks_obtained"] = 5
    await client.post("/api/v1/exams/marks", headers=_h(fx["incharge"]), json=body)
    assert [x.version_no for x in await _versions(db_session, fx, fx["student"])] == [1, 2]


@pytest.mark.asyncio
async def test_enter_marks_without_provenance_is_refused(db_session: AsyncSession):
    from app.modules.examinations.schemas.exam import MarkEntry
    from app.modules.examinations.services.exam_service import ExamService

    fx = await _world(db_session)
    with pytest.raises(ValueError, match="provenance"):
        await ExamService(db_session).enter_marks(
            fx["school"].id, fx["exam"].id,
            [MarkEntry(student_id=fx["student"].id, marks_obtained=Decimal("3"))],
        )


@pytest.mark.asyncio
async def test_historical_marks_baselined_lazily_not_published(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    db_session.add(ExamMark(school_id=fx["school"].id, exam_id=fx["exam"].id,
                            student_id=fx["student"].id, marks_obtained=Decimal("3")))
    await db_session.flush()
    assert await _versions(db_session, fx, fx["student"]) == []
    p = (await _preview(client, fx, fx["principal"])).json()["data"]
    v = await _versions(db_session, fx, fx["student"])
    assert len(v) == 1 and v[0].source == "historical_baseline"
    assert await db_session.scalar(select(func.count()).select_from(ExamResultPublished)) == 0
    # Second preview creates nothing more (idempotent).
    await _preview(client, fx, fx["principal"])
    assert len(await _versions(db_session, fx, fx["student"])) == 1
    r = await _confirm(client, fx, fx["principal"], p, confirm_partial=True,
                       acknowledged_pending_count=p["pending_total"])
    assert r.status_code == 200, r.text
    assert r.json()["data"]["release"]["generation_no"] == 1


def test_preview_token_binding_expiry_and_tamper():
    sid, eid, uid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    tok = issue_preview_token(school_id=sid, exam_id=eid, actor_id=uid, fingerprint="f" * 64,
                              action_token=uuid.uuid4())
    assert verify_preview_token(tok, school_id=sid, exam_id=eid, actor_id=uid)["fp"] == "f" * 64
    for kw, code in (
        (dict(school_id=uuid.uuid4(), exam_id=eid, actor_id=uid), "invalid_preview"),
        (dict(school_id=sid, exam_id=uuid.uuid4(), actor_id=uid), "invalid_preview"),
        (dict(school_id=sid, exam_id=eid, actor_id=uuid.uuid4()), "preview_not_yours"),
        (dict(school_id=sid, exam_id=eid, actor_id=uid, now=time.time() + 3600),
         "preview_expired"),
    ):
        with pytest.raises(ReleaseError) as e:
            verify_preview_token(tok, **kw)
        assert e.value.code == code
    body, mac = tok.split(".")
    with pytest.raises(ReleaseError):
        verify_preview_token(body + "x." + mac, school_id=sid, exam_id=eid, actor_id=uid)


@pytest.mark.asyncio
async def test_preview_token_cannot_be_used_by_other_actor(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    await _evaluate_and_approve(client, fx, fx["student"], ANSWERS_GOOD, fx["incharge"])
    p = (await _preview(client, fx, fx["incharge"])).json()["data"]
    r = await _confirm(client, fx, fx["principal"], p, confirm_partial=True,
                       acknowledged_pending_count=p["pending_total"])
    assert r.status_code == 403 and r.json()["code"] == "preview_not_yours"


@pytest.mark.asyncio
async def test_learner_results_cross_family_and_staff_denied(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    # Student 1 cannot read student 2 via the parent route; parent not linked to s2.
    r = await client.get(f"/api/v1/portal/child/{fx['student2'].id}/results",
                         headers=_h(fx["parent_user"]))
    assert r.status_code == 403
    r = await client.get(f"/api/v1/portal/child/{fx['student'].id}/results",
                         headers=_h(fx["student_user"]))
    assert r.status_code == 403
    r = await client.get("/api/v1/portal/results", headers=_h(fx["incharge"]))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_cross_tenant_exam_release_404(client: AsyncClient, db_session: AsyncSession):
    fx = await _world(db_session)
    other = School(name="Other", code="OTH", tenant_slug="other", board="SSC",
                   contact_email="o@o.com", contact_phone="+910000000999", is_active=True)
    db_session.add(other)
    await db_session.flush()
    foreign = await _user(db_session, other, UserRole.SUPER_ADMIN, "foreign_p", "+910000000998")
    r = await client.post(f"/api/v1/exams/{fx['exam'].id}/release/preview",
                          headers={**auth_headers(access_token_for(foreign, tenant_slug="other")),
                                   "X-Tenant-Slug": "other"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_composite_fk_rejects_cross_tenant_version(db_session: AsyncSession):
    fx = await _world(db_session)
    other = School(name="Other2", code="OT2", tenant_slug="other2", board="SSC",
                   contact_email="o2@o.com", contact_phone="+910000000997", is_active=True)
    db_session.add(other)
    await db_session.flush()
    from datetime import datetime, timezone

    db_session.add(ExamResultVersion(
        school_id=other.id, exam_id=fx["exam"].id, student_id=fx["student"].id, version_no=1,
        marks_obtained=Decimal("1"), source="manual_entry", approved_by=fx["incharge"].id,
        approved_at=datetime.now(timezone.utc),
    ))
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            await db_session.flush()


@pytest.mark.asyncio
async def test_misconceptions_learner_visible_only_for_published_revision(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    s1 = fx["student"]
    await _evaluate_and_approve(client, fx, s1, ANSWERS_WEAK, fx["incharge"])
    entries = (await db_session.execute(select(MisconceptionEntry).where(
        MisconceptionEntry.student_id == s1.id))).scalars().all()
    assert entries and all(e.source_evaluation_revision_id for e in entries)
    kw = dict(school_id=fx["school"].id, student_id=s1.id)
    assert await published_misconceptions_for_student(db_session, **kw) == []
    p = (await _preview(client, fx, fx["incharge"])).json()["data"]
    await _confirm(client, fx, fx["incharge"], p, confirm_partial=True,
                   acknowledged_pending_count=p["pending_total"])
    assert len(await published_misconceptions_for_student(db_session, **kw)) == len(entries)
    # Reopen + re-approve: entries now point at the new revision, which is NOT published →
    # hidden again (no "later version" leniency).
    mark = (await db_session.execute(select(ExamMark).where(
        ExamMark.exam_id == fx["exam"].id, ExamMark.student_id == s1.id))).scalar_one()
    await client.post(f"/api/v1/exams/evaluations/{mark.source_evaluation_id}/reopen",
                      headers=_h(fx["incharge"]), json={"reason": "Recheck"})
    await client.post(f"/api/v1/exams/evaluations/{mark.source_evaluation_id}/approve",
                      headers=_h(fx["incharge"]), json={"teacher_overrides": {}})
    assert await published_misconceptions_for_student(db_session, **kw) == []


@pytest.mark.asyncio
async def test_multi_page_answer_sheet_limits(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    from app.db.models.file import FileCategory, UploadedFile

    svc = "app.modules.examinations.services.answer_sheet_eval_service"
    monkeypatch.setattr(f"{svc}.read_file_bytes_bounded", lambda *_a, **_k: b"\x89PNG")

    async def _no_ocr(**_kwargs):  # OCR stays inert (P-R3); teacher answers are used
        return {}, None

    monkeypatch.setattr(f"{svc}.extract_answers_from_image", _no_ocr)
    fx = await _world(db_session)

    async def _file(school, size=1000, mime="image/png", cat=FileCategory.ANSWER_SHEET):
        f = UploadedFile(school_id=school.id, filename="p.png", original_name="p.png",
                         content_type=mime, size_bytes=size, category=cat, storage_path="x",
                         url="x", uploaded_by=fx["incharge"].id)
        db_session.add(f)
        await db_session.flush()
        return f.id

    url = f"/api/v1/exams/{fx['exam'].id}/evaluations"
    base = {"student_id": str(fx["student"].id), "student_answers": ANSWERS_GOOD}
    pages = [str(await _file(fx["school"])) for _ in range(3)]
    r = await client.post(url, headers=_h(fx["teacher"]), json={**base, "page_file_ids": pages})
    assert r.status_code == 201, r.text
    assert r.json()["data"]["page_file_ids"] == pages
    # Second sheet for an approved student requires reopen; first approve it.
    eid = r.json()["data"]["id"]
    await client.post(f"/api/v1/exams/evaluations/{eid}/approve", headers=_h(fx["teacher"]),
                      json={"teacher_overrides": {}})
    r = await client.post(url, headers=_h(fx["teacher"]), json={**base, "page_file_ids": pages})
    assert r.status_code == 400 and "reopen" in r.json()["detail"]

    s2 = {**base, "student_id": str(fx["student2"].id)}
    dup = await _file(fx["school"])
    r = await client.post(url, headers=_h(fx["teacher"]),
                          json={**s2, "page_file_ids": [str(dup), str(dup)]})
    assert r.status_code == 400 and "more than once" in r.json()["detail"]
    too_many = [str(await _file(fx["school"])) for _ in range(13)]
    r = await client.post(url, headers=_h(fx["teacher"]), json={**s2, "page_file_ids": too_many})
    assert r.status_code == 422  # schema max_length=12
    pdf = await _file(fx["school"], mime="application/pdf")
    r = await client.post(url, headers=_h(fx["teacher"]), json={**s2, "page_file_ids": [str(pdf)]})
    assert r.status_code == 400 and "image" in r.json()["detail"]
    big = await _file(fx["school"], size=6 * 1024 * 1024)
    r = await client.post(url, headers=_h(fx["teacher"]), json={**s2, "page_file_ids": [str(big)]})
    assert r.status_code == 400 and "5 MB" in r.json()["detail"]
    other = School(name="O3", code="O3", tenant_slug="o3", board="SSC",
                   contact_email="o3@o.com", contact_phone="+910000000996", is_active=True)
    db_session.add(other)
    await db_session.flush()
    foreign = await _file(other)
    r = await client.post(url, headers=_h(fx["teacher"]),
                          json={**s2, "page_file_ids": [str(foreign)]})
    assert r.status_code == 400 and "not found" in r.json()["detail"]
