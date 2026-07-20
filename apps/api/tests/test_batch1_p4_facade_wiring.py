"""Batch 1 P4 — facade wiring for question papers and lesson plans."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.staff_permissions import StaffScope
from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.gateway import LLMResult
from app.modules.ai.services.question_paper_service import generate_paper
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.curriculum.services.curriculum_grounding import CurriculumGrounding
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService

_QP_LLM = "app.modules.ai.services.question_paper_service.generate_llm"
_COPILOT_LLM = "app.modules.ai.services.teacher_copilot_service.generate_llm"


def _stub_embedder() -> EmbeddingService:
    return EmbeddingService(provider=StubEmbeddingProvider())


async def _seed_approved(db):
    school = School(
        name="P4 School",
        code="p4",
        tenant_slug="p4",
        board="SSC",
        contact_email="p4@t.com",
        contact_phone="+910000000099",
        is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id,
        mobile="+910000000098",
        full_name="P4 Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()
    pack = CurriculumPack(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        academic_year_id=ay.id,
        board="SSC",
        book_title="Maths",
        created_by=teacher.id,
        status=PackStatus.APPROVED,
        version=3,
        approved_by=teacher.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(pack)
    await db.flush()
    ch = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(ch)
    await db.flush()
    db.add(
        CurriculumTopic(
            school_id=school.id,
            chapter_id=ch.id,
            title="Linear Equations",
            concepts=["slope"],
            order_index=0,
        )
    )
    await db.flush()
    return {
        "school": school,
        "cls": cls,
        "teacher": teacher,
        "maths": maths,
        "pack": pack,
    }


def _teacher_scope(ids) -> StaffScope:
    return StaffScope(
        user_id=ids["teacher"].id,
        role=UserRole.TEACHER.value,
        teaching_pairs={(ids["cls"].id, ids["maths"].id)},
        incharge_class_ids=set(),
        is_admin=False,
    )


async def _seed_in_fixtures(db, test_school, test_class, academic_year, teacher_user):
    """Seed approved pack in the same tenant as conftest fixtures (for HTTP tests)."""
    maths = Subject(school_id=test_school.id, name="Maths", class_id=test_class.id, code="M-P4")
    db.add(maths)
    await db.flush()
    pack = CurriculumPack(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=maths.id,
        academic_year_id=academic_year.id,
        board="SSC",
        book_title="Maths",
        created_by=teacher_user.id,
        status=PackStatus.APPROVED,
        version=3,
        approved_by=teacher_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(pack)
    await db.flush()
    ch = CurriculumChapter(
        school_id=test_school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(ch)
    await db.flush()
    db.add(
        CurriculumTopic(
            school_id=test_school.id,
            chapter_id=ch.id,
            title="Linear Equations",
            concepts=["slope"],
            order_index=0,
        )
    )
    await db.flush()
    return {
        "school": test_school,
        "cls": test_class,
        "teacher": teacher_user,
        "maths": maths,
        "pack": pack,
    }


_GROUNDED_PAPER = {
    "title": "Maths — 10",
    "general_instructions": ["Answer all questions."],
    "sections": [
        {
            "title": "Section I",
            "questions": [
                {
                    "number": "1",
                    "text": "Solve 2x + 3 = 7.",
                    "marks": 2,
                    "type": "short",
                    "answer_key": "x = 2",
                    "citations": [1],
                }
            ],
        }
    ],
}


@pytest.mark.asyncio
async def test_question_paper_uses_ground_approved_pack_facade(db_session, monkeypatch):
    ids = await _seed_approved(db_session)
    flag = {"called": False}

    async def _fake_llm(*_args, **_kwargs):
        flag["called"] = True
        return LLMResult(
            text=json.dumps(_GROUNDED_PAPER),
            provider="stub",
            model="stub-model",
            tokens_in=10,
            tokens_out=20,
            latency_ms=1,
        )

    monkeypatch.setattr(_QP_LLM, _fake_llm)

    with patch(
        "app.modules.ai.services.question_paper_service.ground_approved_pack",
        new_callable=AsyncMock,
    ) as mock_facade:
        real = __import__(
            "app.modules.curriculum.services.curriculum_grounding",
            fromlist=["ground_approved_pack"],
        ).ground_approved_pack
        mock_facade.side_effect = real

        paper = await generate_paper(
            db_session,
            school_id=ids["school"].id,
            created_by=ids["teacher"].id,
            class_id=ids["cls"].id,
            subject_id=ids["maths"].id,
            topics=["Linear Equations"],
            total_marks=80,
            duration_minutes=180,
            difficulty="balanced",
            credits_charged=0,
            pack_id=ids["pack"].id,
            embedder=_stub_embedder(),
            store=InMemoryVectorStore(),
        )

        mock_facade.assert_awaited_once()
        assert flag["called"] is True
        assert paper.grounded is True
        assert paper.pack_id == ids["pack"].id
        assert paper.grounding_sources
        assert paper.grounding_sources[0]["pack_status"] == "approved"
        assert paper.grounding_sources[0]["pack_version"] == 3


@pytest.mark.asyncio
async def test_lesson_plan_template_mode_via_facade(db_session):
    ids = await _seed_approved(db_session)
    svc = LessonPlanService(db_session)
    plan = await svc.generate(
        ids["school"].id,
        _teacher_scope(ids),
        class_id=ids["cls"].id,
        subject_id=ids["maths"].id,
        topic="Linear Equations",
        pack_id=ids["pack"].id,
        embedder=_stub_embedder(),
        store=InMemoryVectorStore(),
    )
    assert plan.grounded is True
    assert plan.pack_id == ids["pack"].id
    assert plan.ai_model == "template-v1-grounded"
    assert plan.grounding_sources
    assert plan.grounding_sources[0]["pack_status"] == "approved"


@pytest.mark.asyncio
async def test_lesson_plan_endpoint_template_mode(
    client, admin_user, db_session, test_school, test_class, academic_year, teacher_user
):
    from tests.conftest import auth_headers, get_auth_token

    ids = await _seed_in_fixtures(
        db_session, test_school, test_class, academic_year, teacher_user
    )
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/lesson-plans/generate",
        headers=auth_headers(token),
        json={
            "class_id": str(ids["cls"].id),
            "subject_id": str(ids["maths"].id),
            "topic": "Linear Equations",
            "pack_id": str(ids["pack"].id),
            "generation_mode": "template",
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    data = body.get("data") or body
    assert data["grounded"] is True
    assert data["pack_status"] == "approved"
    assert data["pack_version"] == 3
    assert data["grounded_at"] is not None


@pytest.mark.asyncio
async def test_lesson_plan_endpoint_copilot_mode(
    db_session,
    client,
    admin_user,
    monkeypatch,
    test_school,
    test_class,
    academic_year,
    teacher_user,
):
    from tests.conftest import auth_headers, get_auth_token

    ids = await _seed_in_fixtures(
        db_session, test_school, test_class, academic_year, teacher_user
    )

    async def _fake_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps(
                {
                    "title": "Copilot plan",
                    "segments": [
                        {"duration_min": 10, "activity": "Intro", "citations": [1]},
                        {"duration_min": 20, "activity": "Practice", "citations": [1]},
                    ],
                    "notes": "Grounded notes",
                }
            ),
            provider="stub",
            model="stub-copilot",
            tokens_in=5,
            tokens_out=10,
            latency_ms=1,
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/lesson-plans/generate",
        headers=auth_headers(token),
        json={
            "class_id": str(ids["cls"].id),
            "subject_id": str(ids["maths"].id),
            "topic": "Linear Equations",
            "pack_id": str(ids["pack"].id),
            "generation_mode": "copilot",
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json().get("data") or resp.json()
    assert data["grounded"] is True
    assert data["ai_model"] is not None
    assert "copilot" in data["ai_model"].lower() or "stub" in data["ai_model"].lower()


@pytest.mark.asyncio
async def test_question_paper_api_returns_provenance_for_badge(
    client,
    admin_user,
    db_session,
    monkeypatch,
    test_school,
    test_class,
    academic_year,
    teacher_user,
):
    from tests.conftest import auth_headers, get_auth_token

    ids = await _seed_in_fixtures(
        db_session, test_school, test_class, academic_year, teacher_user
    )

    async def _fake_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps(_GROUNDED_PAPER),
            provider="stub",
            model="stub-model",
            tokens_in=10,
            tokens_out=20,
            latency_ms=1,
        )

    monkeypatch.setattr(_QP_LLM, _fake_llm)

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.post(
        "/api/v1/ai/question-papers/generate",
        headers=auth_headers(token),
        json={
            "class_id": str(ids["cls"].id),
            "subject_id": str(ids["maths"].id),
            "topics": ["Linear Equations"],
            "total_marks": 80,
            "duration_minutes": 180,
            "pack_id": str(ids["pack"].id),
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json().get("data") or resp.json()
    assert data["grounded"] is True
    assert data["pack_status"] == "approved"
    assert data["pack_version"] == 3
    assert data["grounded_at"] is not None


@pytest.mark.asyncio
async def test_curriculum_grounding_badge_provenance_helper():
    from app.modules.curriculum.schemas.provenance import provenance_from_sources

    prov = provenance_from_sources(
        [{"pack_status": "approved", "pack_version": 2, "chapter": "Algebra"}],
        pack_id="abc",
        grounded=True,
        created_at=datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc),
    )
    assert prov["pack_status"] == "approved"
    assert prov["pack_version"] == 2
    assert prov["grounded"] is True
    assert prov["grounded_at"] is not None
