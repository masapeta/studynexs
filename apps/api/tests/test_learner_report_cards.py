"""Learner report cards (Stage 2): approved + every manifest exam released, published figures only."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.report_card import ReportCard
from app.modules.ai.gateway.base import LLMResult
from tests.test_exam_result_release import (
    ANSWERS_GOOD,
    ANSWERS_WEAK,
    _confirm,
    _deterministic_grading,  # noqa: F401  (autouse: offline subjective grading)
    _evaluate_and_approve,
    _h,
    _preview,
    _world,
)


@pytest.fixture(autouse=True)
def _offline_remark(monkeypatch):
    async def _fake(messages, **_kw):
        return LLMResult(
            text="Steady effort; keep revising.", provider="test", model="fixed",
            tokens_in=1, tokens_out=1, latency_ms=1,
        )

    monkeypatch.setattr("app.modules.ai.services.report_card_service.generate_llm", _fake)


async def _generate(client, fx, actor, student) -> dict:
    r = await client.post(
        "/api/v1/ai/report-cards/generate", headers=_h(actor),
        json={"student_id": str(student.id), "title": "Term 1"},
    )
    assert r.status_code == 200, r.text
    return r.json()


async def _approve(client, fx, actor, report_id):
    r = await client.post(f"/api/v1/ai/report-cards/{report_id}/approve", headers=_h(actor))
    assert r.status_code == 200, r.text


async def _release_all(client, fx, actor):
    p = (await _preview(client, fx, actor)).json()["data"]
    r = await _confirm(client, fx, actor, p, confirm_partial=True,
                       acknowledged_pending_count=p["pending_total"])
    assert r.status_code == 200, r.text
    return r.json()["data"]


async def _student_cards(client, fx):
    r = await client.get("/api/v1/portal/report-cards", headers=_h(fx["student_user"]))
    assert r.status_code == 200, r.text
    return r.json()["data"]


async def _parent_cards(client, fx):
    r = await client.get(f"/api/v1/portal/child/{fx['student'].id}/report-cards",
                         headers=_h(fx["parent_user"]))
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.mark.asyncio
async def test_card_hidden_until_approved_and_results_released(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    incharge, s1 = fx["incharge"], fx["student"]
    await _evaluate_and_approve(client, fx, s1, ANSWERS_GOOD, incharge)
    card = await _generate(client, fx, incharge, s1)
    stored = await db_session.get(ReportCard, uuid.UUID(card["id"]))
    assert stored.exam_ids == [str(fx["exam"].id)]

    # Draft + unreleased → hidden from both learner roles; detail 404.
    assert await _student_cards(client, fx) == []
    assert await _parent_cards(client, fx) == []
    r = await client.get(f"/api/v1/portal/report-cards/{card['id']}", headers=_h(fx["student_user"]))
    assert r.status_code == 404

    # Approved but results still unreleased → still hidden.
    await _approve(client, fx, incharge, card["id"])
    assert await _student_cards(client, fx) == []

    # Released → visible with published figures and the approved remark.
    await _release_all(client, fx, incharge)
    rows = await _student_cards(client, fx)
    assert [c["id"] for c in rows] == [card["id"]]
    assert rows[0]["total_obtained"] == card["total_obtained"]
    assert rows[0]["remark"] == "Steady effort; keep revising."
    assert rows[0]["remark_withheld"] is False
    assert (await _parent_cards(client, fx))[0]["percentage"] == rows[0]["percentage"]
    r = await client.get(f"/api/v1/portal/child/{s1.id}/report-cards/{card['id']}",
                         headers=_h(fx["parent_user"]))
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_card_uses_published_version_not_working_marks(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    incharge, s1, exam = fx["incharge"], fx["student"], fx["exam"]
    eid = await _evaluate_and_approve(client, fx, s1, ANSWERS_WEAK, incharge)
    await _release_all(client, fx, incharge)
    released = (await client.get(f"/api/v1/portal/results/{exam.id}",
                                 headers=_h(fx["student_user"]))).json()["data"]["marks_obtained"]

    # Staff change marks (new immutable version, not yet released) then generate + approve.
    await client.post(f"/api/v1/exams/evaluations/{eid}/reopen", headers=_h(incharge),
                      json={"reason": "Recheck"})
    r = await client.post(f"/api/v1/exams/evaluations/{eid}/approve", headers=_h(incharge),
                          json={"teacher_overrides": {"3": {"marks": 2, "reason": "partial"}}})
    assert r.status_code == 200, r.text
    card = await _generate(client, fx, incharge, s1)
    await _approve(client, fx, incharge, card["id"])
    assert card["total_obtained"] != released

    # Learner sees the RELEASED figure; the remark written for the new marks is withheld.
    rows = await _student_cards(client, fx)
    assert rows[0]["total_obtained"] == released
    assert rows[0]["remark"] is None and rows[0]["remark_withheld"] is True

    # After the re-release the figures and remark line up again.
    await _release_all(client, fx, incharge)
    rows = await _student_cards(client, fx)
    assert rows[0]["total_obtained"] == card["total_obtained"]
    assert rows[0]["remark_withheld"] is False


@pytest.mark.asyncio
async def test_withdraw_and_block_hide_card(client: AsyncClient, db_session: AsyncSession):
    fx = await _world(db_session)
    incharge, admin, principal = fx["incharge"], fx["admin"], fx["principal"]
    await _evaluate_and_approve(client, fx, fx["student"], ANSWERS_GOOD, incharge)
    await _release_all(client, fx, incharge)
    card = await _generate(client, fx, incharge, fx["student"])
    await _approve(client, fx, incharge, card["id"])
    assert len(await _student_cards(client, fx)) == 1

    exam_id = fx["exam"].id
    r = await client.post(f"/api/v1/exams/{exam_id}/release/block", headers=_h(principal),
                          json={"reason": "Review", "action_token": str(uuid.uuid4())})
    assert r.status_code == 200
    assert await _student_cards(client, fx) == []
    await client.post(f"/api/v1/exams/{exam_id}/release/unblock", headers=_h(principal),
                      json={"reason": "Done", "action_token": str(uuid.uuid4())})
    assert len(await _student_cards(client, fx)) == 1

    r = await client.post(f"/api/v1/exams/{exam_id}/release/withdraw", headers=_h(admin),
                          json={"reason": "Error", "action_token": str(uuid.uuid4())})
    assert r.status_code == 200
    assert await _student_cards(client, fx) == []
    assert await _parent_cards(client, fx) == []


@pytest.mark.asyncio
async def test_partial_release_of_card_exams_hides_card(
    client: AsyncClient, db_session: AsyncSession
):
    """A card whose manifest includes an exam with no visible result stays hidden."""
    fx = await _world(db_session)
    incharge = fx["incharge"]
    await _evaluate_and_approve(client, fx, fx["student"], ANSWERS_GOOD, incharge)
    await _release_all(client, fx, incharge)
    card = await _generate(client, fx, incharge, fx["student"])
    await _approve(client, fx, incharge, card["id"])
    stored = await db_session.get(ReportCard, uuid.UUID(card["id"]))
    stored.exam_ids = [*stored.exam_ids, str(uuid.uuid4())]
    await db_session.flush()
    assert await _student_cards(client, fx) == []


@pytest.mark.asyncio
async def test_legacy_card_without_manifest_never_shown(
    client: AsyncClient, db_session: AsyncSession
):
    fx = await _world(db_session)
    incharge = fx["incharge"]
    await _evaluate_and_approve(client, fx, fx["student"], ANSWERS_GOOD, incharge)
    await _release_all(client, fx, incharge)
    card = await _generate(client, fx, incharge, fx["student"])
    await _approve(client, fx, incharge, card["id"])
    stored = await db_session.get(ReportCard, uuid.UUID(card["id"]))
    stored.exam_ids = None
    await db_session.flush()
    assert await _student_cards(client, fx) == []


@pytest.mark.asyncio
async def test_report_card_ownership(client: AsyncClient, db_session: AsyncSession):
    fx = await _world(db_session)
    incharge = fx["incharge"]
    await _evaluate_and_approve(client, fx, fx["student"], ANSWERS_GOOD, incharge)
    await _evaluate_and_approve(client, fx, fx["student2"], ANSWERS_GOOD, incharge)
    await _release_all(client, fx, incharge)
    other = await _generate(client, fx, incharge, fx["student2"])
    await _approve(client, fx, incharge, other["id"])

    # Parent not linked to student2; student1 cannot read student2's card by id.
    r = await client.get(f"/api/v1/portal/child/{fx['student2'].id}/report-cards",
                         headers=_h(fx["parent_user"]))
    assert r.status_code == 403
    r = await client.get(f"/api/v1/portal/report-cards/{other['id']}",
                         headers=_h(fx["student_user"]))
    assert r.status_code == 404
    r = await client.get(
        f"/api/v1/portal/child/{fx['student'].id}/report-cards/{other['id']}",
        headers=_h(fx["parent_user"]),
    )
    assert r.status_code == 404
    # Staff do not use the learner path.
    r = await client.get("/api/v1/portal/report-cards", headers=_h(incharge))
    assert r.status_code == 403
    # Staff output now carries not_assessed (was always []).
    staff = await client.get(f"/api/v1/ai/report-cards/{other['id']}", headers=_h(incharge))
    assert "not_assessed" in staff.json()
    assert (await db_session.execute(select(ReportCard))).scalars().all()
