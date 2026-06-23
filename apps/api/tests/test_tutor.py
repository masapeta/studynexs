"""Tutor API — Mistake Recovery lessons."""
from __future__ import annotations

import pytest

from tests.conftest import access_token_for, auth_headers


@pytest.mark.asyncio
async def test_tutor_recommendations_student(client, student_user, test_school, db_session):
    from sqlalchemy import select

    from app.db.models.student import Student

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = access_token_for(student_user)
    resp = await client.get(
        f"/api/v1/tutor/students/{student.id}/recommendations",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    recs = resp.json()["data"]
    assert len(recs) >= 1
    assert recs[0]["lesson_key"]


@pytest.mark.asyncio
async def test_tutor_lesson_fractions(client, student_user, test_school, db_session):
    from sqlalchemy import select

    from app.db.models.student import Student

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    token = access_token_for(student_user)
    resp = await client.get(
        f"/api/v1/tutor/students/{student.id}/lessons/fractions",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    lesson = resp.json()["data"]
    assert lesson["lesson_key"] == "fractions"
    assert len(lesson["steps"]) >= 3
    assert lesson["steps"][0]["visual_kind"]
