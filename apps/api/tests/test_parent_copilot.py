"""Parent Copilot — grounded briefings (Batch 27)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.academic import Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.mastery import MasteryTrend, StudentTopicMastery
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.gateway import LLMResult
from app.modules.ai.rag import RagService
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)
from app.modules.parent_copilot.services.parent_copilot_service import ParentCopilotService
from tests.conftest import access_token_for, auth_headers

_COPILOT_LLM = "app.modules.parent_copilot.services.parent_copilot_service.generate_llm"


async def _seed_parent_copilot(
    db,
    parent_user: User,
    student_user: User,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    student = (
        await db.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()

    subject = Subject(school_id=test_school.id, name="Maths", class_id=test_class.id)
    db.add(subject)
    await db.flush()

    db.add(
        StudentTopicMastery(
            school_id=test_school.id,
            student_id=student.id,
            subject_id=subject.id,
            class_id=test_class.id,
            academic_year_id=academic_year.id,
            topic="linear_equations",
            topic_display="Linear Equations",
            mastery_pct=52.0,
            class_avg_pct=70.0,
            assessments_count=2,
            trend=MasteryTrend.STABLE,
        )
    )
    await db.flush()

    pack = CurriculumPack(
        school_id=test_school.id, class_id=test_class.id, subject_id=subject.id,
        academic_year_id=academic_year.id, board="SSC", created_by=admin_user.id,
        status=PackStatus.APPROVED, approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(pack)
    await db.flush()
    chapter = CurriculumChapter(
        school_id=test_school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(chapter)
    await db.flush()
    topic = CurriculumTopic(
        school_id=test_school.id, chapter_id=chapter.id, title="Linear Equations",
        concepts=["slope"], order_index=0,
    )
    db.add(topic)
    await db.flush()
    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=test_school.id, pack_id=pack.id
    )
    await StudentWeakConceptService(db).sync_from_ledger(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        academic_year_id=academic_year.id,
        ledger_rows=[{
            "student_id": student.id,
            "topic": "linear equations",
            "topic_display": "Linear Equations",
            "mastery_pct": 52.0,
            "class_avg_pct": 70.0,
            "assessments_count": 2,
            "last_assessed_on": date(2026, 7, 1),
            "trend": MasteryTrend.STABLE,
            "history": [],
        }],
    )

    store = InMemoryVectorStore()
    embedder = EmbeddingService(provider=StubEmbeddingProvider())
    await RagService(db, embedder=embedder, store=store).index_pack(pack)
    concept = (
        await db.execute(
            select(CurriculumConcept).where(CurriculumConcept.pack_id == pack.id)
        )
    ).scalar_one()

    return {
        "school": test_school,
        "student": student,
        "parent_user": parent_user,
        "pack": pack,
        "concept": concept,
        "embedder": embedder,
        "store": store,
    }


@pytest.mark.asyncio
async def test_parent_briefing_grounded(
    db_session,
    parent_user,
    student_user,
    test_school,
    test_class,
    academic_year,
    admin_user,
    monkeypatch,
):
    ids = await _seed_parent_copilot(
        db_session, parent_user, student_user, test_school, test_class, academic_year, admin_user
    )

    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({
                "summary": (
                    "Your child is building skills in linear equations but needs practice on "
                    "slope."
                ),
                "focus_areas": [
                    {
                        "topic": "Linear Equations",
                        "subject_name": "Maths",
                        "mastery_pct": 52,
                    }
                ],
                "home_tips": ["Review one worked example together each evening."],
                "encouragement": "Steady practice will help.",
            }),
            model="stub",
            provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)

    out = await ParentCopilotService(db_session).generate_briefing(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        user_id=parent_user.id,
        role="parent",
        embedder=ids["embedder"],
        store=ids["store"],
        credits_charged=0,
    )
    assert out.grounded is True
    assert out.fallback is False
    assert "linear" in out.summary.lower() or out.focus_areas
    assert out.home_tips
    assert out.pack_id == ids["pack"].id
    assert out.concept_id == ids["concept"].id
    assert out.concept_slug == ids["concept"].slug
    assert out.mastery_topic == "Linear Equations"
    assert out.source_count > 0
    assert out.evidence_reason
    assert "approved school curriculum" in out.evidence_summary.lower()


@pytest.mark.asyncio
async def test_parent_ask_api(
    client: AsyncClient,
    db_session,
    parent_user,
    student_user,
    test_school,
    test_class,
    academic_year,
    admin_user,
    monkeypatch,
):
    ids = await _seed_parent_copilot(
        db_session, parent_user, student_user, test_school, test_class, academic_year, admin_user
    )

    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({
                "answer": "Try short daily practice on slope using graph paper.",
                "home_tips": ["Use real-life stairs to explain rise over run."],
            }),
            model="stub",
            provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)

    token = access_token_for(parent_user)
    res = await client.post(
        f"/api/v1/parent-copilot/students/{ids['student'].id}/ask",
        json={"question": "How can I help at home with algebra?"},
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    # API-level unit test does not inject the in-memory vector store used above;
    # runtime certification verifies source_count > 0 against the real RAG store.
    assert body["grounded"] is False
    assert body["fallback"] is False
    assert body["answer"]
    assert body["pack_id"] == str(ids["pack"].id)
    assert body["concept_id"] == str(ids["concept"].id)
    assert body["concept_slug"] == ids["concept"].slug
    assert body["mastery_topic"] == "Linear Equations"
    assert body["source_count"] == 0
    assert body["evidence_reason"]


@pytest.mark.asyncio
async def test_parent_briefing_api(
    client: AsyncClient,
    db_session,
    parent_user,
    student_user,
    test_school,
    test_class,
    academic_year,
    admin_user,
    monkeypatch,
):
    ids = await _seed_parent_copilot(
        db_session, parent_user, student_user, test_school, test_class, academic_year, admin_user
    )

    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({
                "summary": "Focus on linear equations this week.",
                "focus_areas": [],
                "home_tips": ["Practice 15 minutes daily."],
                "encouragement": "Keep going!",
            }),
            model="stub",
            provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)

    token = access_token_for(parent_user)
    res = await client.get(
        f"/api/v1/parent-copilot/students/{ids['student'].id}/briefing",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["summary"]
    assert body["pack_id"] == str(ids["pack"].id)
    assert body["concept_id"] == str(ids["concept"].id)
    assert body["fallback"] is False
    assert body["evidence_summary"]


@pytest.mark.asyncio
async def test_parent_copilot_denies_unlinked_child(
    client: AsyncClient,
    db_session,
    parent_user,
    student_user,
    test_school,
    test_class,
    academic_year,
    admin_user,
    monkeypatch,
):
    await _seed_parent_copilot(
        db_session, parent_user, student_user, test_school, test_class, academic_year, admin_user
    )
    other_user = User(
        school_id=test_school.id,
        username="other_student",
        mobile="+919876543299",
        full_name="Other Student",
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()
    other_student = Student(
        school_id=test_school.id,
        user_id=other_user.id,
        class_id=test_class.id,
        admission_no="ADM002",
        roll_no="2",
    )
    db_session.add(other_student)
    await db_session.flush()

    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({"answer": "No access", "home_tips": []}),
            model="stub",
            provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)
    token = access_token_for(parent_user)
    brief = await client.get(
        f"/api/v1/parent-copilot/students/{other_student.id}/briefing",
        headers=auth_headers(token),
    )
    ask = await client.post(
        f"/api/v1/parent-copilot/students/{other_student.id}/ask",
        json={"question": "How can I help?"},
        headers=auth_headers(token),
    )
    assert brief.status_code == 403
    assert ask.status_code == 403


@pytest.mark.asyncio
async def test_parent_briefing_marks_deterministic_fallback(
    db_session,
    parent_user,
    student_user,
    test_school,
    test_class,
    academic_year,
    admin_user,
    monkeypatch,
):
    ids = await _seed_parent_copilot(
        db_session, parent_user, student_user, test_school, test_class, academic_year, admin_user
    )

    async def _bad_llm(*_a, **_k):
        return LLMResult(text="not json", model="stub", provider="stub")

    monkeypatch.setattr(_COPILOT_LLM, _bad_llm)
    out = await ParentCopilotService(db_session).generate_briefing(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        user_id=parent_user.id,
        role="parent",
        embedder=ids["embedder"],
        store=ids["store"],
        credits_charged=0,
    )
    assert out.grounded is True
    assert out.fallback is True
    assert out.pack_id == ids["pack"].id
    assert out.concept_id == ids["concept"].id
