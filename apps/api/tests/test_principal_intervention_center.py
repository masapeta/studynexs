"""Principal Intelligence — Intervention Center dashboard contract."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import TeacherSubjectMapping
from app.db.models.user import User
from tests.conftest import access_token_for, auth_headers
from tests.test_mastery_flags import _seed_flagging_scenario


@pytest.mark.asyncio
async def test_principal_dashboard_surfaces_actionable_intervention(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    teacher_user: User,
    student_user: User,
    test_school,
    test_class,
):
    _weak, subject, _token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    test_class.class_incharge_id = teacher_user.id
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=subject.id,
            class_id=test_class.id,
            is_primary=True,
        )
    )
    await db_session.flush()

    resp = await client.get(
        "/api/v1/dashboard/summary",
        headers=auth_headers(access_token_for(admin_user)),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    interventions = data["principal_interventions"]
    assert interventions

    card = interventions[0]
    assert card["id"].startswith("mastery_flag:")
    assert card["severity"] in {"high", "medium"}
    assert "Algebra" in card["issue"]
    assert "mastery" in card["why_it_matters"].lower()
    assert "Maths" in card["affected_scope"]
    assert card["owner"] == teacher_user.full_name
    assert "human-led remediation" in card["recommended_intervention"]
    assert card["href"].startswith("/dashboard/teaching/mastery")
    assert card["evidence_chain_href"].startswith("/api/v1/mastery/flags/")
    assert card["evidence"]
    evidence_labels = {item["label"] for item in card["evidence"]}
    assert {"Mastery", "Assessment evidence", "Teacher review"}.issubset(evidence_labels)


@pytest.mark.asyncio
async def test_teacher_dashboard_does_not_receive_principal_interventions(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    teacher_user: User,
    student_user: User,
    test_school,
    test_class,
):
    await _seed_flagging_scenario(client, db_session, test_school, test_class, student_user)

    resp = await client.get(
        "/api/v1/dashboard/summary",
        headers=auth_headers(access_token_for(teacher_user)),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["persona"] == "teacher"
    assert data["principal_interventions"] == []
