"""Student Copilot — grounded study assistance (Batch 25)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.mastery import MasteryTrend
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
from app.modules.tutor.schemas.copilot import CopilotAnswerOut, CopilotAskIn
from app.modules.tutor.services.student_copilot_service import StudentCopilotService
from tests.conftest import access_token_for, auth_headers

_COPILOT_LLM = "app.modules.tutor.services.student_copilot_service.generate_llm"


async def _seed_copilot(db, *, mastery_pct=55.0):
    school = School(
        name="T", code="T", tenant_slug="t", board="SSC",
        contact_email="a@t.com", contact_phone="+910000000000", is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id, mobile="+910000000001", full_name="T",
        role=UserRole.TEACHER, is_active=True,
    )
    student_user = User(
        school_id=school.id, mobile="+910000000002", full_name="S",
        role=UserRole.STUDENT, is_active=True,
    )
    db.add_all([cls, teacher, student_user])
    await db.flush()
    subject = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(subject)
    await db.flush()
    student = Student(
        school_id=school.id, user_id=student_user.id, class_id=cls.id,
        admission_no="A1",
    )
    db.add(student)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id, class_id=cls.id, subject_id=subject.id,
        academic_year_id=ay.id, board="SSC", created_by=teacher.id,
        status=PackStatus.APPROVED, approved_by=teacher.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(pack)
    await db.flush()
    chapter = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(chapter)
    await db.flush()
    topic = CurriculumTopic(
        school_id=school.id, chapter_id=chapter.id, title="Linear Equations",
        concepts=["slope"], order_index=0,
    )
    db.add(topic)
    await db.flush()
    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )

    await StudentWeakConceptService(db).sync_from_ledger(
        school_id=school.id,
        class_id=cls.id,
        subject_id=subject.id,
        academic_year_id=ay.id,
        ledger_rows=[{
            "student_id": student.id,
            "topic": "linear equations",
            "topic_display": "Linear Equations",
            "mastery_pct": mastery_pct,
            "class_avg_pct": 72.0,
            "assessments_count": 2,
            "last_assessed_on": date(2026, 7, 1),
            "trend": MasteryTrend.STABLE,
            "history": [],
        }],
    )

    concept = (
        await db.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == "slope")
        )
    ).scalar_one()
    card = ConceptCard(
        school_id=school.id, pack_id=pack.id, concept_id=concept.id,
        title="Slope", explanation="Slope is rise over run.",
        status=ConceptCardStatus.APPROVED, created_by=teacher.id,
        approved_by=teacher.id, approved_at=datetime.now(timezone.utc),
    )
    db.add(card)
    await db.flush()

    store = InMemoryVectorStore()
    embedder = EmbeddingService(provider=StubEmbeddingProvider())
    await RagService(db, embedder=embedder, store=store).index_pack(pack)

    return {
        "school": school,
        "student": student,
        "student_user": student_user,
        "pack": pack,
        "concept": concept,
        "embedder": embedder,
        "store": store,
    }


@pytest.mark.asyncio
async def test_study_context_lists_weak_concepts(db_session):
    ids = await _seed_copilot(db_session)
    ctx = await StudentCopilotService(db_session).get_study_context(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        embedder=ids["embedder"],
        store=ids["store"],
    )
    assert ctx.weak_concepts
    assert ctx.primary_concept_slug == "slope"
    assert ctx.grounded is True
    assert ctx.weak_concepts[0].pack_id == ids["pack"].id
    assert ctx.weak_concepts[0].mastery_topic == "Linear Equations"


@pytest.mark.asyncio
async def test_ask_grounded_answer(db_session, monkeypatch):
    ids = await _seed_copilot(db_session)

    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({
                "answer": "Slope tells you how steep a line is.",
                "citations": [1],
                "follow_up_hints": ["Try graphing y = 2x + 1"],
            }),
            model="stub",
            provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)

    out = await StudentCopilotService(db_session).ask(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        body=CopilotAskIn(question="What is slope?", concept_slug="slope"),
        user_id=ids["student_user"].id,
        role="student",
        embedder=ids["embedder"],
        store=ids["store"],
        credits_charged=0,
    )
    assert out.grounded is True
    assert "slope" in out.answer.lower()
    assert out.concept_slug == "slope"
    assert out.pack_id == ids["pack"].id
    assert out.concept_id == ids["concept"].id
    assert out.source_count > 0


@pytest.mark.asyncio
async def test_study_context_api(client: AsyncClient, db_session):
    ids = await _seed_copilot(db_session)
    token = access_token_for(ids["student_user"])
    res = await client.get(
        f"/api/v1/tutor/students/{ids['student'].id}/study-context",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["primary_concept_slug"] == "slope"
    assert len(body["weak_concepts"]) >= 1
    assert body["weak_concepts"][0]["pack_id"] == str(ids["pack"].id)


@pytest.mark.asyncio
async def test_daily_plan_uses_approved_learning_evidence(db_session):
    ids = await _seed_copilot(db_session)
    plan = await StudentCopilotService(db_session).get_daily_plan(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        embedder=ids["embedder"],
        store=ids["store"],
    )

    assert plan.status == "ready"
    assert plan.fallback is False
    assert plan.grounded is True
    assert plan.lesson_key == "slope"
    assert plan.pack_id == ids["pack"].id
    assert plan.concept_id == ids["concept"].id
    assert plan.mastery_topic == "Linear Equations"
    assert plan.mastery_pct == 55.0


@pytest.mark.asyncio
async def test_daily_plan_empty_state_is_not_demo_fallback(db_session):
    ids = await _seed_copilot(db_session, mastery_pct=85.0)
    plan = await StudentCopilotService(db_session).get_daily_plan(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        embedder=ids["embedder"],
        store=ids["store"],
    )

    assert plan.status == "empty"
    assert plan.fallback is False
    assert plan.grounded is False
    assert plan.lesson_key is None
    assert "No weak concept evidence" in plan.evidence_summary


@pytest.mark.asyncio
async def test_daily_plan_api_is_student_scoped(client: AsyncClient, db_session):
    ids = await _seed_copilot(db_session)
    token = access_token_for(ids["student_user"])

    res = await client.get(
        f"/api/v1/tutor/students/{ids['student'].id}/daily-plan",
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["status"] == "ready"
    assert body["lesson_key"] == "slope"
    assert body["pack_id"] == str(ids["pack"].id)
    assert body["mastery_topic"] == "Linear Equations"
    assert body["fallback"] is False

    other_user = User(
        school_id=ids["school"].id,
        mobile="+910000000099",
        full_name="Other Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()
    other_student = Student(
        school_id=ids["school"].id,
        user_id=other_user.id,
        class_id=ids["student"].class_id,
        admission_no="A2",
    )
    db_session.add(other_student)
    await db_session.flush()
    other_token = access_token_for(other_user)

    denied = await client.get(
        f"/api/v1/tutor/students/{ids['student'].id}/daily-plan",
        headers=auth_headers(other_token),
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_student_copilot_ask_api_uses_current_user_id(
    client: AsyncClient, db_session, monkeypatch
):
    ids = await _seed_copilot(db_session)
    token = access_token_for(ids["student_user"])
    seen = {}

    async def _fake_ask(self, *, user_id, **kwargs):
        seen["user_id"] = user_id
        return CopilotAnswerOut(
            answer="Slope is rise over run.",
            concept_slug="slope",
            pack_id=ids["pack"].id,
            concept_id=ids["concept"].id,
            source_count=1,
            grounded=True,
        )

    monkeypatch.setattr(StudentCopilotService, "ask", _fake_ask)

    res = await client.post(
        f"/api/v1/tutor/students/{ids['student'].id}/ask",
        headers=auth_headers(token),
        json={"question": "What is slope?", "concept_slug": "slope"},
    )

    assert res.status_code == 200, res.text
    assert seen["user_id"] == ids["student_user"].id
    body = res.json()["data"]
    assert body["pack_id"] == str(ids["pack"].id)


@pytest.mark.asyncio
async def test_recommendations_prioritize_graph_weak_concepts(db_session):
    ids = await _seed_copilot(db_session)
    from app.modules.tutor.services.tutor_service import list_recommendations

    recs = await list_recommendations(
        db_session, school_id=ids["school"].id, student_id=ids["student"].id
    )
    assert recs[0].lesson_key == "slope"
    assert recs[0].source == "concept_card"
    assert recs[0].pack_id == ids["pack"].id
    assert recs[0].concept_id == ids["concept"].id


@pytest.mark.asyncio
async def test_tutor_lesson_exposes_concept_card_pack(db_session):
    ids = await _seed_copilot(db_session)
    from app.modules.tutor.services.tutor_service import get_lesson

    lesson = await get_lesson(
        db_session,
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        lesson_key="slope",
    )
    assert lesson is not None
    assert lesson.trigger == "concept_card"
    assert lesson.pack_id == ids["pack"].id
    assert lesson.concept_id == ids["concept"].id
    assert lesson.concept_slug == "slope"


@pytest.mark.asyncio
async def test_tutor_lesson_prefers_student_evidence_when_duplicate_slug_exists(db_session):
    ids = await _seed_copilot(db_session)
    teacher_id = ids["pack"].created_by

    newer_pack = CurriculumPack(
        school_id=ids["school"].id,
        class_id=ids["pack"].class_id,
        subject_id=ids["pack"].subject_id,
        academic_year_id=ids["pack"].academic_year_id,
        board="SSC",
        created_by=teacher_id,
        status=PackStatus.APPROVED,
        approved_by=teacher_id,
        approved_at=datetime.now(timezone.utc),
        version=2,
    )
    db_session.add(newer_pack)
    await db_session.flush()
    chapter = CurriculumChapter(
        school_id=ids["school"].id,
        pack_id=newer_pack.id,
        number="1",
        title="Duplicate Algebra",
        order_index=0,
    )
    db_session.add(chapter)
    await db_session.flush()
    topic = CurriculumTopic(
        school_id=ids["school"].id,
        chapter_id=chapter.id,
        title="Linear Equations",
        concepts=["slope"],
        order_index=0,
    )
    db_session.add(topic)
    await db_session.flush()
    await KnowledgeGraphService(db_session).build_spine_from_pack(
        school_id=ids["school"].id,
        pack_id=newer_pack.id,
    )
    newer_concept = (
        await db_session.execute(
            select(CurriculumConcept).where(
                CurriculumConcept.pack_id == newer_pack.id,
                CurriculumConcept.slug == "slope",
            )
        )
    ).scalar_one()
    db_session.add(
        ConceptCard(
            school_id=ids["school"].id,
            pack_id=newer_pack.id,
            concept_id=newer_concept.id,
            title="Newer Slope",
            explanation="This newer card must not override the student's evidence chain.",
            status=ConceptCardStatus.APPROVED,
            created_by=teacher_id,
            approved_by=teacher_id,
            approved_at=datetime.now(timezone.utc),
        )
    )
    await db_session.flush()

    from app.modules.tutor.services.tutor_service import get_lesson, list_recommendations

    recs = await list_recommendations(
        db_session, school_id=ids["school"].id, student_id=ids["student"].id
    )
    assert recs[0].lesson_key == "slope"
    assert recs[0].pack_id == ids["pack"].id
    assert recs[0].concept_id == ids["concept"].id

    lesson = await get_lesson(
        db_session,
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        lesson_key="slope",
    )

    assert lesson is not None
    assert lesson.trigger == "concept_card"
    assert lesson.pack_id == ids["pack"].id
    assert lesson.concept_id == ids["concept"].id
    assert lesson.concept_slug == "slope"
