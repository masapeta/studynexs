"""Compose question papers from the school-private question bank (qp_from_bank)."""
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.gateway.base import LLMResult
from app.modules.ai.services.question_bank_service import (
    compose_exact_sections_from_plan,
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
    assert gaps == [{
        "section_title": "Section A",
        "instructions": "Answer all.",
        "marks": 2.0,
        "type": "short",
        "count": 1,
    }]
    assert sections[0]["questions"][0]["text"] == "What is 2+2?"
    assert sections[0]["questions"][0]["answer_key"] == "4"


def test_exact_compose_never_relabels_a_question_from_another_chapter() -> None:
    item = QuestionBankItem(
        id=__import__("uuid").uuid4(),
        school_id=__import__("uuid").uuid4(),
        class_id=__import__("uuid").uuid4(),
        subject_id=__import__("uuid").uuid4(),
        source_paper_id=__import__("uuid").uuid4(),
        created_by=__import__("uuid").uuid4(),
        section_title="S",
        question_number="1",
        question_text="A question about motion",
        marks=2,
        question_type="short",
        topics=["Motion"],
        board="SSC",
        grade="10",
        content_fingerprint="motion",
        approval_status="approved",
    )
    plan = [{**MINI_PLAN[0], "count": 1}]
    slots = {(0, 0): {"chapter": "Light", "bloom": "Understand"}}

    sections, used, gaps = compose_exact_sections_from_plan(
        plan, [(item, "Answer")], slots
    )

    assert used == []
    assert sections[0]["questions"] == []
    assert [(gap["chapter"], gap["question_index"]) for gap in gaps] == [
        ("Light", 0)
    ]


@pytest.mark.asyncio
async def test_fetch_compose_candidates_after_approve(db_session):
    scope = await _seed_scope(db_session)
    await _ingest_short_paper(db_session, scope, sections=[{
        "title": "Section A",
        "questions": [
            {
                "number": "1",
                "text": "Q1?",
                "marks": 2,
                "type": "short",
                "answer_key": "A",
                "chapter": "Algebra",
            },
            {
                "number": "2",
                "text": "Q2?",
                "marks": 2,
                "type": "short",
                "answer_key": "B",
                "chapter": "Algebra",
            },
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
            {
                "number": "1", "text": "Q1?", "marks": 2, "type": "short",
                "answer_key": "A", "chapter": "Algebra",
            },
            {
                "number": "2", "text": "Q2?", "marks": 2, "type": "short",
                "answer_key": "B", "chapter": "Algebra",
            },
        ],
    }])
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service._ssc_blueprint",
        lambda _total: MINI_PLAN,
    )
    mock_generate_llm = AsyncMock()
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_llm",
        mock_generate_llm,
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
        section_plan=[{**MINI_PLAN[0], "type": "very_short"}],
        blueprint_slots=[
            {
                "section_index": 0,
                "question_index": 0,
                "chapter": "Algebra",
                "bloom": "Understand",
            },
            {
                "section_index": 0,
                "question_index": 1,
                "chapter": "Algebra",
                "bloom": "Apply",
            },
        ],
    )
    assert paper.ai_model == "bank:compose"
    assert len(paper.sections[0]["questions"]) == 2
    assert all(q["type"] == "very_short" for q in paper.sections[0]["questions"])
    assert paper.sections[0]["questions"][0]["chapter"] == "Algebra"
    assert paper.sections[0]["questions"][1]["bloom"] == "Apply"
    mock_generate_llm.assert_not_called()


@pytest.mark.asyncio
async def test_generate_from_bank_fails_closed_on_exact_blueprint_gap(
    db_session, monkeypatch,
):
    scope = await _seed_scope(db_session)
    await _ingest_short_paper(db_session, scope, sections=[{
        "title": "Section A",
        "questions": [{
            "number": "1",
            "text": "Algebra bank question",
            "marks": 2,
            "type": "short",
            "answer_key": "A",
            "chapter": "Algebra",
        }],
    }])
    mock_generate_llm = AsyncMock(return_value=LLMResult(
        text=(
            '{"fills": [{"section_index": 0, "question_index": 1, '
            '"text": "Light generated question", "marks": 2, '
            '"type": "very_short", "answer_key": "B"}]}'
        ),
        provider="openai",
        model="gpt-test",
        tokens_in=10,
        tokens_out=20,
    ))
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_llm",
        mock_generate_llm,
    )

    with pytest.raises(ValueError, match="approved question bank does not contain enough"):
        await generate_paper_from_bank(
            db_session,
            school_id=scope["school"].id,
            created_by=scope["teacher"].id,
            class_id=scope["cls"].id,
            subject_id=scope["maths"].id,
            topics=["Algebra", "Light"],
            total_marks=4,
            duration_minutes=60,
            difficulty="balanced",
            credits_charged=0,
            section_plan=[{**MINI_PLAN[0], "type": "very_short"}],
            blueprint_slots=[
                {
                    "section_index": 0,
                    "question_index": 0,
                    "chapter": "Algebra",
                    "bloom": "Understand",
                },
                {
                    "section_index": 0,
                    "question_index": 1,
                    "chapter": "Light",
                    "bloom": "Apply",
                },
            ],
        )
    mock_generate_llm.assert_not_called()


@pytest.mark.asyncio
async def test_generate_from_bank_calls_llm_for_gaps(db_session, monkeypatch):
    scope = await _seed_scope(db_session)
    await _ingest_short_paper(db_session, scope, sections=[{
        "title": "Section A",
        "questions": [
            {
                "number": "1",
                "text": "Only one bank Q",
                "marks": 2,
                "type": "short",
                "answer_key": "A",
            },
        ],
    }])
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service._ssc_blueprint",
        lambda _total: MINI_PLAN,
    )
    mock_generate_llm = AsyncMock(return_value=LLMResult(
        text='{"fills": [{"section_title": "Section A", "questions": ['
        '{"number": "2", "text": "LLM gap Q", "marks": 2, "type": "short", "answer_key": "X"}]}]}',
        provider="openai",
        model="gpt-test",
        tokens_in=10,
        tokens_out=20,
    ))
    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_llm",
        mock_generate_llm,
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
    mock_generate_llm.assert_called_once()


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
