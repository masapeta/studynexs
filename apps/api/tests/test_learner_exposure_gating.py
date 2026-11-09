"""E1–E18 learner exposure gating against APPROVED-but-UNRELEASED marks (plan Rev 2 §4).

One world: the student's weak result on topic "Science" is approved and the mastery ledgers are
recomputed, so the staff audience has evidence. Every learner path (parent, student, tutor,
copilots, assistant tools, notifications, report cards, weak concepts) must expose nothing of it
until release. After release, a representative subset must show it — proving the "absent"
assertions are not vacuous.
"""
from __future__ import annotations

import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mastery import AUDIENCE_LEARNER, AUDIENCE_STAFF, StudentTopicMastery
from app.db.models.notification import Notification
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.gateway import LLMResult
from app.modules.mastery.services.mastery_service import recompute_class_subject
from app.modules.workspace.assistant import capabilities as cap
from tests.test_exam_result_release import (
    ANSWERS_WEAK,
    _confirm,
    _deterministic_grading,  # noqa: F401  (autouse)
    _evaluate_and_approve,
    _h,
    _preview,
    _world,
)

TOPIC = "Science"


@pytest.mark.asyncio
async def test_e9_tutor_lesson_hides_unreleased_evidence(
    client: AsyncClient, db_session: AsyncSession
):
    """E9: the lesson for the weak topic carries no mastery % or exam mistake until release."""
    from app.modules.tutor.services.lesson_templates import slugify_lesson_key

    fx = await _world(db_session)
    s1, incharge = fx["student"], fx["incharge"]
    await _evaluate_and_approve(client, fx, s1, ANSWERS_WEAK, incharge)
    await _recompute(db_session, fx)
    url = f"/api/v1/tutor/students/{s1.id}/lessons/{slugify_lesson_key(TOPIC)}"

    def _evidence(resp) -> tuple:
        if resp.status_code == 404:
            return (None, None, None)
        d = resp.json()["data"]
        return (d.get("mastery_pct"), d.get("mistake_summary"), d.get("trigger"))

    for who in (fx["student_user"], fx["parent_user"]):
        r = await client.get(url, headers=_h(who))
        assert r.status_code in (200, 404), r.text
        pct, mistake, trigger = _evidence(r)
        assert pct is None and mistake is None, f"unreleased evidence in lesson: {r.text[:300]}"
        assert trigger not in ("weak_topic", "exam_mistake", "concept_card")

    p = (await _preview(client, fx, incharge)).json()["data"]
    await _confirm(client, fx, incharge, p, confirm_partial=True,
                   acknowledged_pending_count=p["pending_total"])
    await _recompute(db_session, fx)
    r = await client.get(url, headers=_h(fx["student_user"]))
    assert r.status_code == 200, r.text
    pct, mistake, trigger = _evidence(r)
    assert pct is not None or mistake is not None, "released evidence must reach the lesson"
    assert trigger in ("weak_topic", "exam_mistake", "concept_card")


@pytest.mark.asyncio
async def test_e16_e17_staff_only_paths_deny_learners(
    client: AsyncClient, db_session: AsyncSession
):
    """E16 search + E17 learning-evidence: learner roles get 403; staff in scope get 200."""
    from app.db.models.mastery import MasteryFlag
    from app.modules.workspace.assistant.tools import tools_for_role

    fx = await _world(db_session)
    await _evaluate_and_approve(client, fx, fx["student"], ANSWERS_WEAK, fx["incharge"])
    await _recompute(db_session, fx)
    learners = (fx["student_user"], fx["parent_user"])
    for who in learners:
        for url in ("/api/v1/users?search=a", "/api/v1/academic/students?search=a",
                    f"/api/v1/academic/students?class_id={fx['class'].id}&search=a"):
            r = await client.get(url, headers=_h(who))
            assert r.status_code == 403, f"E16 {url} -> {r.status_code}"
    for role in ("student", "parent"):
        assert "student_learning_evidence" not in {t.name for t in tools_for_role(role)}
    from app.db.models.mastery import FlagSeverity

    # One datapoint never raises a flag; seed one so the evidence-chain gate is exercised.
    flag = MasteryFlag(
        school_id=fx["school"].id, student_id=fx["student"].id, class_id=fx["class"].id,
        subject_id=fx["subject"].id, academic_year_id=fx["academic_year"].id,
        topic="science", topic_display=TOPIC, severity=FlagSeverity.HIGH,
    )
    db_session.add(flag)
    await db_session.flush()
    for who in learners:
        r = await client.get(f"/api/v1/mastery/flags/{flag.id}/evidence-chain", headers=_h(who))
        assert r.status_code == 403, f"E17 evidence-chain -> {r.status_code}"
    r = await client.get(f"/api/v1/mastery/flags/{flag.id}/evidence-chain",
                         headers=_h(fx["incharge"]))
    assert r.status_code == 200, r.text
    r = await client.get("/api/v1/academic/students?search=Ravi", headers=_h(fx["incharge"]))
    assert r.status_code == 200


@pytest.fixture(autouse=True)
def _offline_ai(monkeypatch):
    """Hermetic: stub embeddings, and record every prompt the copilots would send."""
    monkeypatch.setattr(
        "app.modules.ai.embeddings.service.get_embedding_provider",
        lambda *a, **k: StubEmbeddingProvider(),
    )
    prompts: list[str] = []

    async def _llm(messages, **_kw):
        prompts.append("\n".join(m.content for m in messages))
        return LLMResult(text="OK.", provider="test", model="fixed", tokens_in=1, tokens_out=1)

    for target in (
        "app.modules.tutor.services.student_copilot_service.generate_llm",
        "app.modules.parent_copilot.services.parent_copilot_service.generate_llm",
    ):
        monkeypatch.setattr(target, _llm, raising=False)
    return prompts


class _U:
    def __init__(self, user, role):
        self.id = str(user.id)
        self.school_id = str(user.school_id)
        self.role = role
        self.full_name = user.full_name
        self.tenant_slug = "test"


def _blob(x) -> str:
    return json.dumps(x, default=str)


async def _recompute(db, fx):
    await recompute_class_subject(db, fx["school"].id, fx["class"].id, fx["subject"].id)


async def _learner_surfaces(client: AsyncClient, db: AsyncSession, fx) -> dict[str, str]:
    """Every learner-facing read for student 1, serialized. Keys are the E-inventory ids."""
    sid = fx["student"].id
    stu, par = _h(fx["student_user"]), _h(fx["parent_user"])
    out: dict[str, str] = {}

    async def get(key, url, headers):
        r = await client.get(url, headers=headers)
        assert r.status_code == 200, f"{key} {url}: {r.status_code} {r.text}"
        out[key] = r.text

    await get("E1:children-progress", "/api/v1/portal/parent/children-progress", par)
    await get("E2:child-summary", f"/api/v1/portal/child/{sid}/summary", par)
    await get("E2/E3:child-progress", f"/api/v1/portal/child/{sid}/progress", par)
    await get("E4:mastery-student", f"/api/v1/mastery/students/{sid}", stu)
    await get("E4:mastery-parent", f"/api/v1/mastery/students/{sid}", par)
    await get("E5:daily-plan", f"/api/v1/tutor/students/{sid}/daily-plan", stu)
    await get("E6:study-context", f"/api/v1/tutor/students/{sid}/study-context", stu)
    await get("E8:tutor-recs", f"/api/v1/tutor/students/{sid}/recommendations", stu)
    await get("E13:results", "/api/v1/portal/results", stu)
    await get("E14:report-cards-student", "/api/v1/portal/report-cards", stu)
    await get("E14:report-cards-parent", f"/api/v1/portal/child/{sid}/report-cards", par)
    await get("E15:notifications-student", "/api/v1/notifications", stu)
    await get("E15:notifications-parent", "/api/v1/notifications", par)
    await get("E18:weak-concepts-student", f"/api/v1/curriculum/students/{sid}/weak-concepts", stu)
    await get("E18:weak-concepts-parent", f"/api/v1/curriculum/students/{sid}/weak-concepts", par)

    su, pu = _U(fx["student_user"], "student"), _U(fx["parent_user"], "parent")
    out["E11:assistant-child-progress"] = _blob(await cap.my_child_progress(db, pu, {}))
    out["E11:assistant-children-overview"] = _blob(await cap.my_children_overview(db, pu, {}))
    out["E12:assistant-daily-plan"] = _blob(await cap.my_daily_plan(db, su, {}))
    out["E12:assistant-weak-topics"] = _blob(await cap.my_weak_topics(db, su, {}))
    return out


def _mastery_figures(text: str) -> list:
    data = json.loads(text)["data"]
    return [t for s in data.get("subjects", []) for t in s.get("topics", [])]


@pytest.mark.asyncio
async def test_unreleased_marks_reach_no_learner_path(
    client: AsyncClient, db_session: AsyncSession, _offline_ai
):
    fx = await _world(db_session)
    s1, incharge = fx["student"], fx["incharge"]
    await _evaluate_and_approve(client, fx, s1, ANSWERS_WEAK, incharge)
    await _recompute(db_session, fx)

    staff_rows = (await db_session.execute(select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == s1.id,
        StudentTopicMastery.audience == AUDIENCE_STAFF))).scalars().all()
    assert staff_rows, "precondition: staff ledger must hold the unreleased evidence"
    staff_view = await client.get(f"/api/v1/mastery/students/{s1.id}", headers=_h(incharge))
    assert _mastery_figures(staff_view.text), "precondition: staff sees it before release"

    before = await _learner_surfaces(client, db_session, fx)
    leaks = {k: v for k, v in before.items() if TOPIC.lower() in v.lower()
             and not k.startswith(("E13", "E15"))}
    assert leaks == {}, f"unreleased topic exposed on: {sorted(leaks)}"
    # E13 lists the exam title only, as pending, with no figures.
    results = json.loads(before["E13:results"])["data"]
    mine = [r for r in results if r["exam_id"] == str(fx["exam"].id)][0]
    assert mine["status"] == "pending" and mine["marks_obtained"] is None
    assert _mastery_figures(before["E4:mastery-student"]) == []
    assert _mastery_figures(before["E4:mastery-parent"]) == []
    # E15: no release notifications for learners before a real generation.
    learner_ids = {fx["student_user"].id, fx["parent_user"].id}
    assert (await db_session.execute(select(Notification).where(
        Notification.user_id.in_(learner_ids)))).scalars().all() == []

    # E7 / E10: copilot prompts must not carry the unreleased topic.
    _offline_ai.clear()
    # 400 "no weak concept" is the gated outcome: the copilot finds no learner evidence.
    r = await client.post(f"/api/v1/tutor/students/{s1.id}/ask", headers=_h(fx["student_user"]),
                          json={"question": "What should I revise?"})
    assert r.status_code in (200, 400), r.text
    assert TOPIC.lower() not in r.text.lower()
    r = await client.post(f"/api/v1/parent-copilot/students/{s1.id}/ask",
                          headers=_h(fx["parent_user"]),
                          json={"question": "Where is my child weak?"})
    assert r.status_code in (200, 400), r.text
    assert TOPIC.lower() not in r.text.lower()
    assert all(TOPIC.lower() not in p.lower() for p in _offline_ai), "copilot prompt leak"

    # Release → the learner ledger and the main learner views now carry it.
    p = (await _preview(client, fx, incharge)).json()["data"]
    r = await _confirm(client, fx, incharge, p, confirm_partial=True,
                       acknowledged_pending_count=p["pending_total"])
    assert r.status_code == 200, r.text
    await _recompute(db_session, fx)
    assert (await db_session.execute(select(StudentTopicMastery).where(
        StudentTopicMastery.student_id == s1.id,
        StudentTopicMastery.audience == AUDIENCE_LEARNER))).scalars().all()

    after = await _learner_surfaces(client, db_session, fx)
    assert _mastery_figures(after["E4:mastery-student"]), "E4 must show released mastery"
    assert _mastery_figures(after["E4:mastery-parent"])
    mine = [r for r in json.loads(after["E13:results"])["data"]
            if r["exam_id"] == str(fx["exam"].id)][0]
    assert mine["status"] == "released" and mine["marks_obtained"] is not None
    assert TOPIC.lower() in after["E12:assistant-weak-topics"].lower()
    assert TOPIC.lower() in after["E8:tutor-recs"].lower()
    assert TOPIC.lower() in after["E1:children-progress"].lower()
    assert (await db_session.execute(select(Notification).where(
        Notification.user_id.in_(learner_ids)))).scalars().all()
