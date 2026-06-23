"""Question bank ingest — split approved papers into reusable QuestionBankItem rows."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.question_bank import QuestionBankItem, RubricBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.services.question_bank_service import (
    BankIngestError,
    content_fingerprint,
    count_bank_items_for_paper,
    ingest_from_paper,
)
from tests.conftest import access_token_for, auth_headers

SECTIONS = [
    {
        "title": "Section A",
        "instructions": "Answer all.",
        "questions": [
            {
                "number": "1",
                "text": "What is 2+2?",
                "marks": 2,
                "type": "short",
                "answer_key": "4",
            },
            {
                "number": "2",
                "text": "Define photosynthesis.",
                "marks": 3,
                "type": "long",
                "answer_key": "Process by which plants make food using sunlight.",
            },
        ],
    },
    {
        "title": "Section B",
        "instructions": "MCQ.",
        "questions": [
            {
                "number": "3",
                "text": "Capital of India?",
                "marks": 1,
                "type": "mcq",
                "options": ["Mumbai", "Delhi", "Kolkata", "Chennai"],
                "answer_key": "B",
            },
        ],
    },
]


async def _seed_paper(db, *, status=PaperStatus.DRAFT, sections=None):
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
    author = User(
        school_id=school.id, mobile="+910000000001", full_name="Author",
        role=UserRole.TEACHER, is_active=True,
    )
    approver = User(
        school_id=school.id, mobile="+910000000002", full_name="Approver",
        role=UserRole.CLASS_INCHARGE, is_active=True,
    )
    db.add_all([cls, author, approver])
    await db.flush()
    cls.class_incharge_id = approver.id
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        created_by=author.id,
        title="Unit Test 1",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=Decimal("6"),
        duration_minutes=60,
        topics=["Arithmetic", "Biology"],
        sections=sections if sections is not None else SECTIONS,
        status=status,
        ai_model="openai:gpt-4o-mini",
    )
    db.add(paper)
    await db.flush()
    return {"paper": paper, "approver": approver, "school": school, "cls": cls}


@pytest.mark.asyncio
async def test_ingest_creates_items_and_rubrics(db_session):
    ids = await _seed_paper(db_session)
    paper = ids["paper"]
    now = datetime.now(timezone.utc)

    items = await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now,
    )

    assert len(items) == 3
    assert await count_bank_items_for_paper(db_session, paper.id) == 3

    rubric_count = await db_session.scalar(select(func.count()).select_from(RubricBankItem))
    assert rubric_count == 3

    first = items[0]
    assert first.school_id == paper.school_id
    assert first.section_title == "Section A"
    assert first.question_number == "1"
    assert first.approval_status == "approved"
    assert str(paper.id) in first.used_in_paper_ids
    assert first.content_fingerprint == content_fingerprint(
        question_text="What is 2+2?", marks=2.0, question_type="short",
    )


@pytest.mark.asyncio
async def test_ingest_assigns_position_when_question_number_missing(db_session):
    ids = await _seed_paper(db_session)
    paper = ids["paper"]
    paper.sections = [{
        "title": "Section A",
        "questions": [
            {"number": "", "text": "First?", "marks": 1, "type": "short", "answer_key": "A"},
            {"number": "", "text": "Second?", "marks": 1, "type": "short", "answer_key": "B"},
        ],
    }]
    now = datetime.now(timezone.utc)

    items = await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now,
    )
    numbers = [item.question_number for item in items]
    assert numbers == ["1", "2"]


@pytest.mark.asyncio
async def test_ingest_raises_when_no_valid_questions(db_session):
    ids = await _seed_paper(db_session)
    paper = ids["paper"]
    paper.sections = [{
        "title": "S",
        "questions": [{"number": "1", "text": "  ", "marks": 1, "type": "short"}],
    }]
    now = datetime.now(timezone.utc)

    with pytest.raises(BankIngestError, match="no valid questions"):
        await ingest_from_paper(
            db_session, paper, approved_by=ids["approver"].id, approved_at=now,
        )


@pytest.mark.asyncio
async def test_ingest_raises_when_sections_empty(db_session):
    ids = await _seed_paper(db_session)
    paper = ids["paper"]
    paper.sections = []
    now = datetime.now(timezone.utc)

    with pytest.raises(BankIngestError, match="no sections"):
        await ingest_from_paper(
            db_session, paper, approved_by=ids["approver"].id, approved_at=now,
        )


@pytest.mark.asyncio
async def test_re_approve_replaces_prior_bank_items(db_session):
    ids = await _seed_paper(db_session)
    paper = ids["paper"]
    now = datetime.now(timezone.utc)

    await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now,
    )
    assert await count_bank_items_for_paper(db_session, paper.id) == 3

    paper.sections[0]["questions"][0]["text"] = "What is 3+3?"
    await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now,
    )

    assert await count_bank_items_for_paper(db_session, paper.id) == 3
    updated = await db_session.scalar(
        select(QuestionBankItem).where(
            QuestionBankItem.source_paper_id == paper.id,
            QuestionBankItem.question_number == "1",
        )
    )
    assert updated.question_text == "What is 3+3?"

    total_bank = await db_session.scalar(select(func.count()).select_from(QuestionBankItem))
    assert total_bank == 3


@pytest.mark.asyncio
async def test_approve_endpoint_ingests_bank_items(client, db_session):
    """HTTP approve should populate question_bank_items for the paper."""
    ids = await _seed_paper(db_session, status=PaperStatus.PENDING_APPROVAL)
    paper = ids["paper"]
    await db_session.flush()

    token = access_token_for(ids["approver"])
    resp = await client.post(
        f"/api/v1/ai/question-papers/{paper.id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"
    assert await count_bank_items_for_paper(db_session, paper.id) == 3


@pytest.mark.asyncio
async def test_approve_endpoint_rejects_empty_paper(client, db_session):
    ids = await _seed_paper(
        db_session, status=PaperStatus.PENDING_APPROVAL, sections=[],
    )
    paper = ids["paper"]
    await db_session.flush()

    token = access_token_for(ids["approver"])
    resp = await client.post(
        f"/api/v1/ai/question-papers/{paper.id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 400
    assert "question bank" in resp.json()["detail"].lower()
    assert paper.status == PaperStatus.PENDING_APPROVAL
