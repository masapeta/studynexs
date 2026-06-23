"""Compose question papers from the school-private question bank (qp_from_bank)."""
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.gateway.base import LLMResult
from app.modules.ai.services.question_bank_service import (
    compose_sections_from_plan,
    count_compose_candidates,
    fetch_compose_candidates,
)
from app.modules.ai.services.question_paper_service import generate_paper_from_bank

MINI_PLAN = [{
    "title": "Section A",
    "marks_per_q": 2,
    "count": 2,
    "type": "short",
    "instructions": "Answer all.",
}]


async def _seed_scope(db):
    school = School(
        name="T", code="T", tenant_slug="test", board="SSC",
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
        school_id=school.id, mobile="+910000000099", full_name="Teacher",
        role=UserRole.TEACHER, is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()
    return {"school": school, "cls": cls, "maths": maths, "teacher": teacher}


async def _ingest_short_paper(db, scope, *, sections):
    from app.modules.ai.services.question_bank_service import ingest_from_paper

    paper = QuestionPaper(
        school_id=scope["school"].id,
        class_id=scope["cls"].id,
        subject_id=scope["maths"].id,
        created_by=scope["teacher"].id,
        title="Seed",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=Decimal("4"),
        sections=sections,
        status=PaperStatus.APPROVED,
        ai_model="test",
    )
    db.add(paper)
    await db.flush()
    await ingest_from_paper(
        db, paper,
        approved_by=scope["teacher"].id,
        approved_at=datetime.now(timezone.utc),
    )
    return paper


@pytest.mark.asyncio
async def test_compose_picks_bank_items_by_marks_and_type(db_session):
    item = QuestionBankItem(
        school_id=__import__("uuid").uuid4(),
        class_id=__import__("uuid").uuid4(),
        subject_id=__import__("uuid").uuid4(),
        source_paper_id=__import__("uuid").uuid4(),
        created_by=__import__("uuid").uuid4(),
        section_title="S",
        question_number="1",
        question_text="What is 2+2?",
        marks=2,
        question_type="short",
        board="SSC",
        grade="10",
        content_fingerprint="abc",
        approval_status="approved",
    )
    sections, used, gaps = compose_sections_from_plan(
        MINI_PLAN, [(item, "4")]
    )
    assert len(used) == 1
    assert gaps == [{"section_title": "Section A", "instructions": "Answer all.", "marks": 2.0, "type": "short", "count": 1}]
    assert sections[0]["questions"][0]["text"] == "What is 2+2?"
    assert sections[0]["questions"][0]["answer_key"] == "4"


@pytest.mark.asyncio
async def test_fetch_compose_candidates_after_approve(db_session):
    scope = await _seed_scope(db_session)
    await _ingest_short_paper(db_session, scope, sections=[{
        "title": "Section A",
        "questions": [
            {"number": "1", "text": "Q1?", "marks": 2, "type": "short", "answer_key": "A"},
            {"number": "2", "text": "Q2?", "marks": 2, "type": "short", "answer_key": "B"},
        ],
    }])
    count = await count_compose_candidates(
        db_session,
        school_id=scope["school"].id,
        class_id=scope["cls"].id,
        subject_id=scope["maths"].id,
    )
    assert count == 2
    candidates = await fetch_compose_candidates(
        db_session,
        school_id=scope["school"].id,
        class_id=scope["cls"].id,
        subject_id=scope["maths"].id,
    )
    assert len(candidates) == 2


@pytest.mark.asyncio
async def test_generate_from_bank_without_llm_when_bank_covers_plan(
    db_session, monkeypatch,
):
    scope = await _seed_scope(db_session)
    await _ingest_short_paper(db_session, scope, sections=[{
        "title": "Section A",
        "questions": [
            {"number": "1", "text": "Q1?", "marks": 2, "type": "short", "answer_key": "A"},
            {"number": "2", "text": "Q2?", "marks": 2, "type": "short", "answer_key": "B"},
        ],
    }])
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service._ssc_blueprint",
        lambda _total: MINI_PLAN,
    )
    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock()
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.get_provider",
        lambda: mock_provider,
    )

    paper = await generate_paper_from_bank(
        db_session,
        school_id=scope["school"].id,
        created_by=scope["teacher"].id,
        class_id=scope["cls"].id,
        subject_id=scope["maths"].id,
        topics=["Algebra"],
        total_marks=4,
        duration_minutes=60,
        difficulty="balanced",
        credits_charged=2,
    )
    assert paper.ai_model == "bank:compose"
    assert len(paper.sections[0]["questions"]) == 2
    mock_provider.generate.assert_not_called()


@pytest.mark.asyncio
async def test_generate_from_bank_calls_llm_for_gaps(db_session, monkeypatch):
    scope = await _seed_scope(db_session)
    await _ingest_short_paper(db_session, scope, sections=[{
        "title": "Section A",
        "questions": [
            {"number": "1", "text": "Only one bank Q", "marks": 2, "type": "short", "answer_key": "A"},
        ],
    }])
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service._ssc_blueprint",
        lambda _total: MINI_PLAN,
    )
    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock(return_value=LLMResult(
        text='{"fills": [{"section_title": "Section A", "questions": ['
        '{"number": "2", "text": "LLM gap Q", "marks": 2, "type": "short", "answer_key": "X"}]}]}',
        provider="openai",
        model="gpt-test",
        tokens_in=10,
        tokens_out=20,
    ))
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.get_provider",
        lambda: mock_provider,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.default_model",
        lambda: "gpt-test",
    )

    paper = await generate_paper_from_bank(
        db_session,
        school_id=scope["school"].id,
        created_by=scope["teacher"].id,
        class_id=scope["cls"].id,
        subject_id=scope["maths"].id,
        topics=[],
        total_marks=4,
        duration_minutes=60,
        difficulty="balanced",
        credits_charged=2,
    )
    assert len(paper.sections[0]["questions"]) == 2
    texts = {q["text"] for q in paper.sections[0]["questions"]}
    assert "Only one bank Q" in texts
    assert "LLM gap Q" in texts
    mock_provider.generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_from_bank_raises_when_bank_empty(db_session, monkeypatch):
    scope = await _seed_scope(db_session)
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service._ssc_blueprint",
        lambda _total: MINI_PLAN,
    )
    with pytest.raises(ValueError, match="No approved questions"):
        await generate_paper_from_bank(
            db_session,
            school_id=scope["school"].id,
            created_by=scope["teacher"].id,
            class_id=scope["cls"].id,
            subject_id=scope["maths"].id,
            topics=[],
            total_marks=4,
            duration_minutes=60,
            difficulty="balanced",
        )
