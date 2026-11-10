"""Copilot endpoints map an unexpected provider failure to a safe 503, never a 500.

Regression for raise_http_for_llm_error() being called without its required log_event,
which raised TypeError inside the except block (lesson-plan copilot, paper review, feedback).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.db.models.question_paper import PaperStatus, QuestionPaper
from tests.conftest import auth_headers, get_auth_token
from tests.test_batch1_p4_facade_wiring import _seed_in_fixtures

_SVC = "app.modules.ai.services.teacher_copilot_service.TeacherCopilotService"


class _ProviderBoom(Exception):
    """An SDK error type the mapper has no specific branch for (generic path)."""


async def _boom(*_args, **_kwargs):
    raise _ProviderBoom("upstream provider exploded")


@pytest.fixture
async def seeded(db_session, test_school, test_class, academic_year, teacher_user, admin_user):
    return await _seed_in_fixtures(db_session, test_school, test_class, academic_year, teacher_user)


@pytest.fixture
async def admin_headers(client, seeded):
    return auth_headers(await get_auth_token(client, "test_admin", "Admin@123"))


def _assert_safe_503(resp, generic_detail: str) -> None:
    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert body["detail"] == generic_detail
    assert "exploded" not in resp.text


@pytest.mark.asyncio
async def test_lesson_plan_copilot_provider_error_returns_503(
    client, seeded, admin_headers, monkeypatch
):
    monkeypatch.setattr(f"{_SVC}.generate_grounded_lesson_plan", _boom)
    resp = await client.post(
        "/api/v1/lesson-plans/generate",
        headers=admin_headers,
        json={
            "class_id": str(seeded["cls"].id),
            "subject_id": str(seeded["maths"].id),
            "topic": "Linear Equations",
            "pack_id": str(seeded["pack"].id),
            "generation_mode": "copilot",
        },
    )
    _assert_safe_503(resp, "AI generation failed. Please try again later.")


@pytest.mark.asyncio
async def test_copilot_paper_review_provider_error_returns_503(
    client, db_session, seeded, admin_headers, monkeypatch
):
    paper = QuestionPaper(
        school_id=seeded["school"].id,
        class_id=seeded["cls"].id,
        subject_id=seeded["maths"].id,
        created_by=seeded["teacher"].id,
        title="Review me",
        board="SSC",
        grade=seeded["cls"].grade,
        subject_name="Maths",
        total_marks=Decimal("10"),
        duration_minutes=60,
        topics=["Linear Equations"],
        sections=[],
        status=PaperStatus.DRAFT,
    )
    db_session.add(paper)
    await db_session.flush()
    monkeypatch.setattr(f"{_SVC}.review_question_paper", _boom)
    resp = await client.post(
        f"/api/v1/ai/copilot/question-papers/{paper.id}/review", headers=admin_headers
    )
    _assert_safe_503(resp, "AI generation failed. Please try again later.")


@pytest.mark.asyncio
async def test_copilot_feedback_draft_provider_error_returns_503(
    client, seeded, admin_headers, monkeypatch
):
    monkeypatch.setattr(f"{_SVC}.draft_feedback", _boom)
    resp = await client.post(
        "/api/v1/ai/copilot/feedback-draft",
        headers=admin_headers,
        json={
            "class_id": str(seeded["cls"].id),
            "subject_id": str(seeded["maths"].id),
            "pack_id": str(seeded["pack"].id),
            "topic": "Linear Equations",
            "student_answer": "x = 2",
        },
    )
    _assert_safe_503(resp, "AI generation failed. Please try again later.")
