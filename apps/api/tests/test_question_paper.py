"""Duplicate-paper: clone into a fresh editable DRAFT owned by the caller, zero LLM (no
AIUsage), with deep-copied sections and safe class re-targeting. Service-level, no LLM call.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from fastapi import HTTPException

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.ai_usage import AIUsage
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.gateway import LLMResult
from app.modules.ai.services.question_paper_service import duplicate_paper, generate_paper

SECTIONS = [{
    "title": "Section A",
    "instructions": "Answer all questions.",
    "questions": [{"number": "1", "text": "What is 2+2?", "marks": 2, "type": "short",
                   "answer_key": "4"}],
}]


async def _seed(db):
    school = School(name="T", code="T", tenant_slug="t", board="SSC",
                    contact_email="a@t.com", contact_phone="+910000000000", is_active=True)
    db.add(school)
    await db.flush()
    ay = AcademicYear(school_id=school.id, year_label="2026-2027",
                      start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True)
    db.add(ay)
    await db.flush()
    cls_a = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    cls_b = Class(school_id=school.id, grade="9", section="B", academic_year_id=ay.id)
    author = User(school_id=school.id, mobile="+910000000001", full_name="Author",
                  role=UserRole.TEACHER, is_active=True)
    dup = User(school_id=school.id, mobile="+910000000002", full_name="Duplicator",
               role=UserRole.TEACHER, is_active=True)
    db.add_all([cls_a, cls_b, author, dup])
    await db.flush()
    maths_a = Subject(school_id=school.id, name="Maths", class_id=cls_a.id)
    science_b = Subject(school_id=school.id, name="Science", class_id=cls_b.id)
    db.add_all([maths_a, science_b])
    await db.flush()
    paper = QuestionPaper(
        school_id=school.id, class_id=cls_a.id, subject_id=maths_a.id, created_by=author.id,
        title="Midterm", board="SSC", grade="10", subject_name="Maths",
        total_marks=Decimal("80"), duration_minutes=180, topics=["Algebra"],
        difficulty_mix={"easy": 40, "medium": 40, "hard": 20},
        general_instructions="Be neat.", sections=SECTIONS, status=PaperStatus.APPROVED,
        ai_model="openai:gpt-4o-mini",
    )
    db.add(paper)
    await db.flush()
    return {"school": school, "paper": paper, "dup": dup,
            "cls_b": cls_b, "science_b": science_b}


@pytest.mark.asyncio
async def test_duplicate_is_fresh_draft_owned_by_caller_no_usage(db_session):
    ids = await _seed(db_session)
    clone = await duplicate_paper(db_session, source=ids["paper"], created_by=ids["dup"].id)

    assert clone.id != ids["paper"].id
    assert clone.status == PaperStatus.DRAFT          # APPROVED source re-enters review
    assert clone.created_by == ids["dup"].id          # owned by the duplicator, not the author
    assert clone.title == "Midterm (Copy)"
    assert clone.sections == SECTIONS                 # content carried over
    # Same class/subject when not re-targeting.
    assert clone.class_id == ids["paper"].class_id
    # Zero-LLM: a duplicate must record NO AIUsage (else it inflates the /usage dashboard).
    n_usage = await db_session.scalar(select(func.count()).select_from(AIUsage))
    assert n_usage == 0


@pytest.mark.asyncio
async def test_duplicate_sections_are_deep_copied(db_session):
    ids = await _seed(db_session)
    clone = await duplicate_paper(db_session, source=ids["paper"], created_by=ids["dup"].id)

    clone.sections[0]["questions"][0]["text"] = "MUTATED"
    # The source paper's questions must be untouched — independent copy, not a shared reference.
    assert ids["paper"].sections[0]["questions"][0]["text"] == "What is 2+2?"


@pytest.mark.asyncio
async def test_duplicate_retarget_remaps_class_subject_and_snapshots(db_session):
    ids = await _seed(db_session)
    clone = await duplicate_paper(
        db_session, source=ids["paper"], created_by=ids["dup"].id,
        class_id=ids["cls_b"].id, subject_id=ids["science_b"].id,
    )
    assert clone.class_id == ids["cls_b"].id
    assert clone.subject_id == ids["science_b"].id
    # Snapshots refreshed from the NEW class/subject, not copied from the source.
    assert clone.grade == "9"
    assert clone.subject_name == "Science"


@pytest.mark.asyncio
async def test_duplicate_retarget_without_subject_is_rejected(db_session):
    ids = await _seed(db_session)
    with pytest.raises(ValueError):
        await duplicate_paper(
            db_session, source=ids["paper"], created_by=ids["dup"].id,
            class_id=ids["cls_b"].id,  # class change with no subject_id → must reject
        )


@pytest.mark.asyncio
async def test_generate_blocks_before_llm_when_qp_cap_reached(db_session, monkeypatch):
    """Credits must be reserved before the provider runs — never after cost is spent."""
    ids = await _seed(db_session)
    paper = ids["paper"]
    author = paper.created_by

    for _ in range(5):
        db_session.add(
            AIUsage(
                school_id=paper.school_id,
                created_by=author,
                feature="question_paper",
                provider="test",
                model="test",
                purpose_tag="qp_full",
                credits_charged=5,
                role="teacher",
            )
        )
    await db_session.flush()

    llm_called = False

    async def fake_generate_llm(*_args, **_kwargs):
        nonlocal llm_called
        llm_called = True
        return LLMResult(
            text="{}",
            provider="test",
            model="test-model",
            tokens_in=1,
            tokens_out=1,
            latency_ms=1,
        )

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_llm",
        fake_generate_llm,
    )

    with pytest.raises(HTTPException) as exc:
        await generate_paper(
            db_session,
            school_id=paper.school_id,
            created_by=author,
            class_id=paper.class_id,
            subject_id=paper.subject_id,
            topics=["Algebra"],
            total_marks=80,
            duration_minutes=180,
            difficulty="balanced",
            role="teacher",
        )
    assert exc.value.status_code == 429
    assert llm_called is False


@pytest.mark.asyncio
async def test_generate_records_usage_when_json_parse_fails(db_session, monkeypatch):
    """LLM cost is incurred even when the model returns unreadable JSON."""
    ids = await _seed(db_session)

    async def fake_generate_llm(*_args, **_kwargs):
        return LLMResult(
            text="not valid json",
            provider="test",
            model="test-model",
            tokens_in=100,
            tokens_out=50,
            latency_ms=10,
        )

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_llm",
        fake_generate_llm,
    )

    paper = ids["paper"]
    with pytest.raises(ValueError, match="unreadable"):
        await generate_paper(
            db_session,
            school_id=paper.school_id,
            created_by=paper.created_by,
            class_id=paper.class_id,
            subject_id=paper.subject_id,
            topics=["Algebra"],
            total_marks=80,
            duration_minutes=180,
            difficulty="balanced",
            credits_charged=5,
        )

    n_usage = await db_session.scalar(select(func.count()).select_from(AIUsage))
    assert n_usage == 1
    usage = (await db_session.execute(select(AIUsage))).scalar_one()
    assert usage.credits_charged == 5
    assert usage.ref_id is None
    assert usage.purpose_tag == "qp_full"
