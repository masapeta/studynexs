# ruff: noqa: E402, I001
"""Seed the Assessment Intelligence v1.0 Batch G-B browser-proof fixture.

Idempotent. Run after the Reference School seed:

  cd apps/api
  python scripts/seed_reference_school.py
  python scripts/seed_assessment_browser_proof_fixture.py

This creates or repairs the narrow Reference tenant fixture required by
``apps/admin-web/e2e-assessment-intelligence-v1.cjs``:

- approved Grade 6 Science question paper;
- linked Unit Test exam with question schema;
- no marks, evaluations, evidence-ledger rows, product flags, schema changes, or
  UI/API behavior changes.

The fixture is developer/reference proof data. It is not a curriculum claim and
is not wired into production startup.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
_api_root = _scripts_dir.parent
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import Class, Subject
from app.db.models.examination import Exam, ExamType
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from reference_school_config import LOGIN_PRINCIPAL, SCHOOL_BOARD, TENANT_SLUG

FIXTURE_PAPER_TITLE = "Grade 6 General Science FA-I Reference Unit Test"
FIXTURE_EXAM_TITLE = "Grade 6 General Science FA-I Reference Unit Test"
FIXTURE_GRADE = "Class 6"
FIXTURE_SECTION = "A"
FIXTURE_SUBJECT = "Science"
FIXTURE_LANGUAGE = "English"
FIXTURE_CURRICULUM = "Telangana reference material"
FIXTURE_PAPER_TYPE = "Unit Test"
FIXTURE_TOPIC = "Grade 6 General Science FA-I"
FIXTURE_TOTAL_MARKS = Decimal("20")
FIXTURE_DURATION_MINUTES = 45
FIXTURE_EXAM_DATE = date(2026, 7, 29)
FIXTURE_AI_MODEL = "assessment-browser-proof-fixture"

FIXTURE_SECTIONS: list[dict[str, Any]] = [
    {
        "title": "Section A",
        "instructions": "Answer all questions.",
        "questions": [
            {
                "number": "1",
                "text": "Name one source of carbohydrates.",
                "marks": 1,
                "type": "short",
                "answer_key": "Rice, wheat, potato, or another valid carbohydrate-rich food.",
                "topic": "Components of food",
            },
            {
                "number": "2",
                "text": "Which nutrient helps body growth and repair?",
                "marks": 1,
                "type": "short",
                "answer_key": "Proteins.",
                "topic": "Components of food",
            },
            {
                "number": "3",
                "text": "Write one example of a protective food.",
                "marks": 1,
                "type": "short",
                "answer_key": "Fruits or vegetables.",
                "topic": "Balanced diet",
            },
            {
                "number": "4",
                "text": "What is roughage?",
                "marks": 1,
                "type": "short",
                "answer_key": "Dietary fibre that helps digestion.",
                "topic": "Components of food",
            },
            {
                "number": "5",
                "text": "Name one food item obtained from animals.",
                "marks": 1,
                "type": "short",
                "answer_key": "Milk, egg, meat, fish, or another valid animal food.",
                "topic": "Food and its sources",
            },
            {
                "number": "6",
                "text": "Which vitamin is commonly linked with night blindness when deficient?",
                "marks": 1,
                "type": "short",
                "answer_key": "Vitamin A.",
                "topic": "Deficiency diseases",
            },
        ],
    },
    {
        "title": "Section B",
        "instructions": "Answer in two or three sentences.",
        "questions": [
            {
                "number": "7",
                "text": "Why do growing children need protein-rich food?",
                "marks": 2,
                "type": "short",
                "answer_key": "Protein helps body growth and repairs worn-out tissues.",
                "topic": "Components of food",
            },
            {
                "number": "8",
                "text": "Write two reasons why a balanced diet is important.",
                "marks": 2,
                "type": "short",
                "answer_key": (
                    "It supplies nutrients in the right amounts and helps maintain health, "
                    "growth, and energy."
                ),
                "topic": "Balanced diet",
            },
            {
                "number": "9",
                "text": "Differentiate between energy-giving and body-building foods.",
                "marks": 2,
                "type": "short",
                "answer_key": (
                    "Energy-giving foods contain carbohydrates or fats; body-building foods "
                    "contain proteins."
                ),
                "topic": "Components of food",
            },
            {
                "number": "10",
                "text": "What is a deficiency disease? Give one example.",
                "marks": 2,
                "type": "short",
                "answer_key": (
                    "A disease caused by lack of a nutrient for a long time; examples include "
                    "scurvy, rickets, or night blindness."
                ),
                "topic": "Deficiency diseases",
            },
        ],
    },
    {
        "title": "Section C",
        "instructions": "Answer in brief.",
        "questions": [
            {
                "number": "11",
                "text": "Explain how you would test a food sample for starch.",
                "marks": 3,
                "type": "long",
                "answer_key": (
                    "Add iodine solution to the food sample. A blue-black colour indicates "
                    "the presence of starch."
                ),
                "topic": "Food tests",
            },
            {
                "number": "12",
                "text": "Describe the main components of a healthy balanced meal.",
                "marks": 3,
                "type": "long",
                "answer_key": (
                    "A balanced meal includes carbohydrates, proteins, fats in limited "
                    "quantity, vitamins, minerals, water, and roughage."
                ),
                "topic": "Balanced diet",
            },
        ],
    },
]


def fixture_total_marks() -> Decimal:
    """Return the deterministic total of all fixture question marks."""

    total = Decimal("0")
    for section in FIXTURE_SECTIONS:
        for question in section["questions"]:
            total += Decimal(str(question["marks"]))
    return total


def build_question_schema() -> list[dict[str, Any]]:
    """Build the exam question schema from the approved paper body."""

    return [
        {
            "no": str(question["number"]),
            "max_marks": float(question["marks"]),
            "topic": str(question.get("topic") or FIXTURE_TOPIC),
        }
        for section in FIXTURE_SECTIONS
        for question in section["questions"]
    ]


def fixture_scope() -> dict[str, str]:
    """Return the browser-proof scope expected by the admin-web harness."""

    return {
        "board": SCHOOL_BOARD,
        "curriculum": FIXTURE_CURRICULUM,
        "grade": "6",
        "subject": FIXTURE_SUBJECT,
        "paper_type": FIXTURE_PAPER_TYPE,
        "language": FIXTURE_LANGUAGE,
    }


async def _reference_school(db) -> School | None:
    return (
        await db.execute(select(School).where(School.tenant_slug == TENANT_SLUG))
    ).scalar_one_or_none()


async def _class_6a(db, school: School) -> Class | None:
    exact = (
        await db.execute(
            select(Class).where(
                Class.school_id == school.id,
                Class.grade.in_([FIXTURE_GRADE, "Grade 6"]),
                Class.section == FIXTURE_SECTION,
            )
        )
    ).scalar_one_or_none()
    if exact:
        return exact

    return (
        await db.execute(
            select(Class)
            .where(
                Class.school_id == school.id,
                Class.grade.ilike("%6%"),
            )
            .order_by(Class.section.asc())
        )
    ).scalars().first()


async def _science_subject(db, school: School, cls: Class) -> Subject | None:
    return (
        await db.execute(
            select(Subject).where(
                Subject.school_id == school.id,
                Subject.class_id == cls.id,
                Subject.name.ilike("%science%"),
            )
        )
    ).scalars().first()


async def _fixture_owner(db, school: School) -> User | None:
    principal = (
        await db.execute(
            select(User).where(
                User.school_id == school.id,
                User.username == LOGIN_PRINCIPAL,
            )
        )
    ).scalar_one_or_none()
    if principal:
        return principal

    return (
        await db.execute(
            select(User)
            .where(
                User.school_id == school.id,
                User.role.in_([UserRole.ADMIN, UserRole.CLASS_INCHARGE, UserRole.TEACHER]),
            )
            .order_by(User.created_at.asc())
        )
    ).scalars().first()


async def _upsert_paper(
    db,
    *,
    school: School,
    cls: Class,
    subject: Subject,
    owner: User,
) -> QuestionPaper:
    paper = (
        await db.execute(
            select(QuestionPaper).where(
                QuestionPaper.school_id == school.id,
                QuestionPaper.title == FIXTURE_PAPER_TITLE,
            )
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if paper is None:
        paper = QuestionPaper(
            school_id=school.id,
            class_id=cls.id,
            subject_id=subject.id,
            created_by=owner.id,
            title=FIXTURE_PAPER_TITLE,
            board=SCHOOL_BOARD,
            grade=FIXTURE_GRADE,
            subject_name=FIXTURE_SUBJECT,
            total_marks=FIXTURE_TOTAL_MARKS,
            duration_minutes=FIXTURE_DURATION_MINUTES,
            topics=[
                "Food and its sources",
                "Components of food",
                "Balanced diet",
                "Deficiency diseases",
                "Food tests",
            ],
            sections=FIXTURE_SECTIONS,
            status=PaperStatus.APPROVED,
            ai_model=FIXTURE_AI_MODEL,
            approved_by=owner.id,
            approved_at=now,
            submitted_at=now,
        )
        db.add(paper)
        await db.flush()
        print(f"  + approved Grade 6 Science fixture paper ({paper.id})")
        return paper

    paper.class_id = cls.id
    paper.subject_id = subject.id
    paper.board = SCHOOL_BOARD
    paper.grade = FIXTURE_GRADE
    paper.subject_name = FIXTURE_SUBJECT
    paper.total_marks = FIXTURE_TOTAL_MARKS
    paper.duration_minutes = FIXTURE_DURATION_MINUTES
    paper.topics = [
        "Food and its sources",
        "Components of food",
        "Balanced diet",
        "Deficiency diseases",
        "Food tests",
    ]
    paper.sections = FIXTURE_SECTIONS
    paper.status = PaperStatus.APPROVED
    paper.ai_model = FIXTURE_AI_MODEL
    paper.approved_by = owner.id
    paper.approved_at = paper.approved_at or now
    paper.submitted_at = paper.submitted_at or now
    print(f"  = approved Grade 6 Science fixture paper ready ({paper.id})")
    return paper


async def _upsert_exam(
    db,
    *,
    school: School,
    cls: Class,
    subject: Subject,
    owner: User,
    paper: QuestionPaper,
) -> Exam:
    question_schema = build_question_schema()
    exam = (
        await db.execute(
            select(Exam).where(
                Exam.school_id == school.id,
                Exam.class_id == cls.id,
                Exam.subject_id == subject.id,
                Exam.title == FIXTURE_EXAM_TITLE,
            )
        )
    ).scalar_one_or_none()

    if exam is None:
        exam = Exam(
            school_id=school.id,
            class_id=cls.id,
            subject_id=subject.id,
            exam_type=ExamType.UNIT_TEST,
            title=FIXTURE_EXAM_TITLE,
            total_marks=FIXTURE_TOTAL_MARKS,
            date=FIXTURE_EXAM_DATE,
            topic=FIXTURE_TOPIC,
            question_schema=question_schema,
            source_paper_id=paper.id,
            created_by=owner.id,
        )
        db.add(exam)
        await db.flush()
        print(f"  + linked Grade 6 Science fixture exam ({exam.id})")
        return exam

    exam.exam_type = ExamType.UNIT_TEST
    exam.total_marks = FIXTURE_TOTAL_MARKS
    exam.date = FIXTURE_EXAM_DATE
    exam.topic = FIXTURE_TOPIC
    exam.question_schema = question_schema
    exam.source_paper_id = paper.id
    print(f"  = linked Grade 6 Science fixture exam ready ({exam.id})")
    return exam


async def seed_fixture() -> int:
    """Create or repair the Reference tenant browser-proof fixture."""

    if fixture_total_marks() != FIXTURE_TOTAL_MARKS:
        raise RuntimeError(
            f"Fixture marks mismatch: expected {FIXTURE_TOTAL_MARKS}, "
            f"got {fixture_total_marks()}"
        )

    async with async_session_factory() as db:
        school = await _reference_school(db)
        if school is None:
            print(f"Reference school not found (tenant={TENANT_SLUG}).")
            print("Run: python scripts/seed_reference_school.py")
            return 1

        cls = await _class_6a(db, school)
        if cls is None:
            print("Class 6 not found in Reference tenant.")
            print("Run: python scripts/seed_reference_school.py")
            return 1

        subject = await _science_subject(db, school, cls)
        if subject is None:
            print(f"Science subject not found for {cls.grade}-{cls.section}.")
            print("Run: python scripts/seed_reference_school.py")
            return 1

        owner = await _fixture_owner(db, school)
        if owner is None:
            print("No principal/admin/teacher user found for fixture ownership.")
            print("Run: python scripts/seed_reference_school.py")
            return 1

        paper = await _upsert_paper(
            db,
            school=school,
            cls=cls,
            subject=subject,
            owner=owner,
        )
        exam = await _upsert_exam(
            db,
            school=school,
            cls=cls,
            subject=subject,
            owner=owner,
            paper=paper,
        )
        await db.commit()

    print("\n=== Assessment browser-proof fixture ready ===")
    print(f"Tenant: {TENANT_SLUG}")
    print(f"Scope: {fixture_scope()}")
    print(f"Question paper: {FIXTURE_PAPER_TITLE} ({paper.id})")
    print(f"Linked exam: {FIXTURE_EXAM_TITLE} ({exam.id})")
    print("Next: cd apps/admin-web && npm run e2e-assessment-v1")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(seed_fixture()))


if __name__ == "__main__":
    main()
