"""Teacher Copilot — grounded lesson plans, QP review, feedback drafting.

Uses stub embedder + in-memory vector store + monkeypatched LLM (no live services).
"""
import json
from datetime import date, datetime, timezone

import pytest

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.lesson_plan import LessonPlanStatus
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.gateway import LLMResult
from app.modules.ai.services.assessment_grounding import ground_for_pack
from app.modules.ai.services.teacher_copilot_service import TeacherCopilotService
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore

_COPILOT_LLM = "app.modules.ai.services.teacher_copilot_service.generate_llm"


def _stub_embedder() -> EmbeddingService:
    return EmbeddingService(provider=StubEmbeddingProvider())


async def _seed(db, *, pack_status=PackStatus.APPROVED):
    school = School(
        name="T",
        code="T",
        tenant_slug="t",
        board="SSC",
        contact_email="a@t.com",
        contact_phone="+910000000000",
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
        mobile="+910000000001",
        full_name="Teacher",
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
        created_by=teacher.id,
        status=pack_status,
        approved_by=teacher.id if pack_status == PackStatus.APPROVED else None,
        approved_at=datetime.now(timezone.utc) if pack_status == PackStatus.APPROVED else None,
    )
    db.add(pack)
    await db.flush()
    ch = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(ch)
    await db.flush()
    topic = CurriculumTopic(
        school_id=school.id,
        chapter_id=ch.id,
        title="Quadratic Equations",
        order_index=0,
        concepts=["factorisation", "formula"],
    )
    db.add(topic)
    await db.flush()
    return school, cls, maths, pack, teacher


def _fake_lesson_llm(monkeypatch):
    payload = {
        "title": "10 A — Maths: Quadratic Equations",
        "segments": [
            {"duration_min": 10, "activity": "Introduce quadratic form", "citations": [1]},
            {"duration_min": 15, "activity": "Worked examples", "citations": [1, 2]},
        ],
        "learning_objectives": ["Solve quadratics by factorisation"],
        "notes": "Use board examples.",
    }

    async def _fake(*_a, **_k):
        return LLMResult(text=json.dumps(payload), model="stub", provider="stub")

    monkeypatch.setattr(_COPILOT_LLM, _fake)


def _fake_review_llm(monkeypatch):
    payload = {
        "summary": "Paper aligns with syllabus; two questions need clearer wording.",
        "overall_quality": "needs_work",
        "suggestions": [
            {
                "section_title": "Section I",
                "question_number": "1",
                "issue": "Ambiguous wording",
                "suggestion": "Specify units explicitly.",
                "citations": [1],
            }
        ],
    }

    async def _fake(*_a, **_k):
        return LLMResult(text=json.dumps(payload), model="stub", provider="stub")

    monkeypatch.setattr(_COPILOT_LLM, _fake)


def _fake_feedback_llm(monkeypatch):
    payload = {
        "feedback_draft": "Good attempt at factorisation. Review sign errors in step 2.",
        "strengths": ["Correct method chosen"],
        "improvements": ["Check arithmetic"],
        "citations": [1],
        "tone": "constructive",
    }

    async def _fake(*_a, **_k):
        return LLMResult(text=json.dumps(payload), model="stub", provider="stub")

    monkeypatch.setattr(_COPILOT_LLM, _fake)


@pytest.mark.asyncio
async def test_grounded_lesson_plan(db_session, monkeypatch):
    school, cls, maths, pack, teacher = await _seed(db_session)
    embedder = _stub_embedder()
    store = InMemoryVectorStore()
    grounding = await ground_for_pack(
        db_session, pack=pack, topics=["Quadratic Equations"], embedder=embedder, store=store
    )
    assert not grounding.is_empty

    _fake_lesson_llm(monkeypatch)
    from app.core.staff_permissions import StaffScope

    scope = StaffScope(
        user_id=teacher.id,
        role="teacher",
        teaching_pairs={(cls.id, maths.id)},
        incharge_class_ids=set(),
        is_admin=False,
    )
    svc = TeacherCopilotService(db_session)
    plan = await svc.generate_grounded_lesson_plan(
        school.id,
        scope,
        class_id=cls.id,
        subject_id=maths.id,
        pack_id=pack.id,
        topic="Quadratic Equations",
        created_by=teacher.id,
        credits_charged=0,
        embedder=embedder,
        store=store,
    )
    assert plan.grounded is True
    assert plan.pack_id == pack.id
    assert plan.grounding_sources
    assert len(plan.segments) >= 2
    assert plan.segments[0].get("citations")
    assert plan.status == LessonPlanStatus.DRAFT


@pytest.mark.asyncio
async def test_lesson_plan_refuses_unapproved_pack(db_session):
    school, cls, maths, pack, teacher = await _seed(
        db_session, pack_status=PackStatus.DRAFT
    )
    from app.core.staff_permissions import StaffScope

    scope = StaffScope(
        user_id=teacher.id,
        role="teacher",
        teaching_pairs={(cls.id, maths.id)},
        incharge_class_ids=set(),
        is_admin=False,
    )
    svc = TeacherCopilotService(db_session)
    with pytest.raises(ValueError, match="Approve"):
        await svc.generate_grounded_lesson_plan(
            school.id,
            scope,
            class_id=cls.id,
            subject_id=maths.id,
            pack_id=pack.id,
            topic="Quadratic Equations",
            created_by=teacher.id,
            credits_charged=0,
            embedder=_stub_embedder(),
            store=InMemoryVectorStore(),
        )


@pytest.mark.asyncio
async def test_qp_review_grounded(db_session, monkeypatch):
    school, cls, maths, pack, teacher = await _seed(db_session)
    embedder = _stub_embedder()
    store = InMemoryVectorStore()
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        created_by=teacher.id,
        title="Maths Unit Test",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=80,
        duration_minutes=180,
        topics=["Quadratic Equations"],
        sections=[
            {
                "title": "Section I",
                "questions": [{"number": "1", "text": "Solve x^2-5x+6=0", "marks": 2, "type": "short"}],
            }
        ],
        status=PaperStatus.DRAFT,
        pack_id=pack.id,
        grounded=True,
        grounding_sources=[],
    )
    db_session.add(paper)
    await db_session.flush()

    _fake_review_llm(monkeypatch)
    svc = TeacherCopilotService(db_session)
    result = await svc.review_question_paper(
        school.id,
        paper=paper,
        user_id=teacher.id,
        credits_charged=0,
        embedder=embedder,
        store=store,
    )
    assert result["overall_quality"] == "needs_work"
    assert result["suggestions"]
    assert result["grounding_sources"]


@pytest.mark.asyncio
async def test_qp_review_requires_grounded_paper(db_session):
    school, cls, maths, pack, teacher = await _seed(db_session)
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        created_by=teacher.id,
        title="Free text paper",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=80,
        duration_minutes=180,
        topics=["Algebra"],
        sections=[],
        status=PaperStatus.DRAFT,
        grounded=False,
    )
    db_session.add(paper)
    await db_session.flush()
    svc = TeacherCopilotService(db_session)
    with pytest.raises(ValueError, match="grounded"):
        await svc.review_question_paper(
            school.id, paper=paper, user_id=teacher.id, credits_charged=0
        )


@pytest.mark.asyncio
async def test_feedback_draft(db_session, monkeypatch):
    school, cls, maths, pack, teacher = await _seed(db_session)
    _fake_feedback_llm(monkeypatch)
    svc = TeacherCopilotService(db_session)
    result = await svc.draft_feedback(
        school.id,
        class_id=cls.id,
        subject_id=maths.id,
        pack_id=pack.id,
        topic="Quadratic Equations",
        student_answer="x=2 and x=3 by factorisation",
        rubric="Full marks for correct roots",
        user_id=teacher.id,
        credits_charged=0,
        embedder=_stub_embedder(),
        store=InMemoryVectorStore(),
    )
    assert "factorisation" in result["feedback_draft"].lower()
    assert result["citation_sources"]
