"""Tests — flags review API: approve (mocked LLM), narrative edit, notify, gates."""

import pytest
from sqlalchemy import select

from app.db.models.mastery import MasteryFlag
from app.db.models.notification import Notification
from tests.conftest import auth_headers, get_auth_token
from tests.test_mastery_flags import _seed_flagging_scenario


class _FakeResult:
    text = "Ravi has found Algebra challenging recently. Practising two problems daily will help."
    model = "fake-model"
    provider = "fake"
    tokens_in = 10
    tokens_out = 20
    latency_ms = 5


class _FakeProvider:
    name = "fake"

    async def generate(self, messages, **kwargs):
        return _FakeResult()


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """No real LLM calls in tests — patch the gateway factory + metering."""
    import app.modules.mastery.services.narrative_service as ns

    async def fake_record_usage(db, **kwargs):
        return None

    monkeypatch.setattr(ns, "get_provider", lambda *a, **k: _FakeProvider())
    monkeypatch.setattr(ns, "default_model", lambda: "fake-model")
    monkeypatch.setattr(ns, "record_usage", fake_record_usage)


async def _flag_of(db_session, student_id):
    return (
        await db_session.execute(
            select(MasteryFlag).where(MasteryFlag.student_id == student_id)
        )
    ).scalar_one()


async def _out_of_scope_maths_flag_and_science_teacher_token(
    client, db_session, test_school, test_class, student_user, teacher_user,
):
    """Maths weakness flag + teacher who only teaches Science in the same class."""
    from app.db.models.academic import Subject, TeacherSubjectMapping

    weak, _maths_subject, _ = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)
    science = Subject(
        school_id=test_school.id, class_id=test_class.id, name="Science", code="SCI"
    )
    db_session.add(science)
    await db_session.flush()
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=science.id,
            class_id=test_class.id,
            is_primary=True,
        )
    )
    await db_session.flush()
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    return flag, token


@pytest.mark.asyncio
async def test_approve_drafts_narrative_then_edit_then_notify(
    client, admin_user, student_user, parent_user, test_school, test_class, db_session,
):
    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)

    # Notify before approval → 409.
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/notify", headers=auth_headers(token)
    )
    assert resp.status_code == 409

    # Approve → LLM draft attached, status APPROVED.
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "approved"
    assert "Algebra" in data["narrative"]
    assert data["ai_model"] == "fake-model"

    # Double-approve → 409.
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 409

    # Teacher edits the note.
    resp = await client.put(
        f"/api/v1/mastery/flags/{flag.id}/narrative",
        headers=auth_headers(token),
        json={"narrative": "Edited note for the parent."},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["narrative"] == "Edited note for the parent."

    # Notify → one in-app notification per linked parent user.
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/notify", headers=auth_headers(token)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["parents_notified"] == 1  # parent_user fixture links one parent
    assert body["flag"]["status"] == "notified"

    notifs = (
        await db_session.execute(
            select(Notification).where(Notification.user_id == parent_user.id)
        )
    ).scalars().all()
    assert len(notifs) == 1
    assert notifs[0].body == "Edited note for the parent."
    assert "Algebra" in notifs[0].title


@pytest.mark.asyncio
async def test_flags_list_and_role_gates(
    client, admin_user, student_user, parent_user, test_school, test_class, db_session,
):
    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )

    resp = await client.get(
        "/api/v1/mastery/flags?status=pending_review", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    flags = resp.json()["data"]
    assert len(flags) == 1
    assert flags[0]["student_name"]
    assert flags[0]["class_name"]
    assert flags[0]["evidence"]["history"]

    # Students and parents cannot touch the review pipeline.
    for username, password in (("test_student", "Student@123"), ("test_parent", "Parent@123")):
        bad_token = await get_auth_token(client, username, password)
        resp = await client.get("/api/v1/mastery/flags", headers=auth_headers(bad_token))
        assert resp.status_code == 403, username
        resp = await client.post(
            f"/api/v1/mastery/flags/{flags[0]['id']}/approve", headers=auth_headers(bad_token)
        )
        assert resp.status_code == 403, username


@pytest.mark.asyncio
async def test_teacher_cannot_approve_flag_outside_teaching_scope(
    client, admin_user, teacher_user, student_user, test_school, test_class, db_session,
):
    """Regression: mastery mutations require class+subject teaching scope."""
    flag, token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_dismiss_flag_outside_teaching_scope(
    client, admin_user, teacher_user, student_user, test_school, test_class, db_session,
):
    """Wiring guard: dismiss must call _assert_flag_mutation_scope."""
    flag, token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/dismiss",
        headers=auth_headers(token),
        json={"reason": "not my subject"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_notify_flag_outside_teaching_scope(
    client, admin_user, teacher_user, student_user, test_school, test_class, db_session,
):
    """Wiring guard: notify_parents must call _assert_flag_mutation_scope."""
    flag, wrong_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    approve = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve",
        headers=auth_headers(admin_token),
    )
    assert approve.status_code == 200, approve.text

    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/notify",
        headers=auth_headers(wrong_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_digest_groups_by_student(
    client, admin_user, student_user, test_school, test_class, db_session,
):
    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)
    await client.post(f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(token))

    resp = await client.get(
        f"/api/v1/mastery/digest?class_id={test_class.id}", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    digest = resp.json()["data"]
    assert len(digest["students"]) == 1
    entry = digest["students"][0]
    assert entry["flags"][0]["topic_display"] == "Algebra"
    assert entry["flags"][0]["narrative"]
