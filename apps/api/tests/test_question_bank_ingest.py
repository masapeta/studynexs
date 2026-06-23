"""Bank ingest must not hard-fail when a paper has duplicate question numbers
in a section (would otherwise hit the unique constraint → 409 → approval rollback)."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User
from app.modules.ai.services.question_bank_service import ingest_from_paper


async def _paper_with_dup_numbers(
    db: AsyncSession, school: School, cls: Class, subject: Subject, creator: User
) -> QuestionPaper:
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=subject.id,
        created_by=creator.id,
        title="Dup Numbers Paper",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=Decimal("6"),
        duration_minutes=60,
        topics=["Algebra"],
        sections=[
            {
                "title": "Section A",
                "instructions": "Answer all.",
                "questions": [
                    {"number": "1", "text": "First question", "marks": 2, "type": "short",
                     "answer_key": "a"},
                    # Duplicate number within the same section — malformed but possible.
                    {"number": "1", "text": "Second question", "marks": 2, "type": "short",
                     "answer_key": "b"},
                    # Blank number whose positional fallback (3) is unique.
                    {"number": "", "text": "Third question", "marks": 2, "type": "short"},
                ],
            }
        ],
        status=PaperStatus.APPROVED,
        ai_model="test",
    )
    db.add(paper)
    await db.flush()
    return paper


@pytest.mark.asyncio
async def test_ingest_dedupes_duplicate_question_numbers(
    admin_user: User, test_school: School, test_class: Class, db_session: AsyncSession
):
    subject = Subject(school_id=test_school.id, class_id=test_class.id, name="Maths", code="MTH")
    db_session.add(subject)
    await db_session.flush()

    paper = await _paper_with_dup_numbers(
        db_session, test_school, test_class, subject, admin_user
    )

    # Must not raise IntegrityError on the (paper, section, number) unique constraint.
    items = await ingest_from_paper(
        db_session, paper, approved_by=admin_user.id, approved_at=datetime.now(timezone.utc)
    )
    assert len(items) == 3

    rows = (
        await db_session.execute(
            select(QuestionBankItem.question_number).where(
                QuestionBankItem.source_paper_id == paper.id
            )
        )
    ).all()
    numbers = [r[0] for r in rows]
    # All three landed with distinct numbers within the section (dedupe applied).
    assert len(numbers) == 3
    assert len(set(numbers)) == 3
    assert "1" in numbers and "1.1" in numbers
