"""Demo v1 assets for Reference School — closes Journey 2/3/4 seed gaps.

Idempotent. Run after seed_reference_school_curriculum.py:
  python scripts/seed_reference_school_demo_v1.py

Creates:
  - Approved grounded question paper (Class 10 Maths — Quadratic Equations)
  - Pending-approval paper for principal briefing queue (optional incharge review)
  - Unit test exam linked to approved paper + AI eval in ``suggested`` status
  - Parent/student "Class work" notice for Quadratic Equations practice
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
_api_root = _scripts_dir.parent
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_SUGGESTED,
    AnswerSheetEvaluation,
)
from app.db.models.misconception import MisconceptionEntry
from app.db.models.communication import Notice, NoticeAudience, NoticePriority
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import CurriculumPack, CurriculumTopic, PackStatus
from app.db.models.examination import Exam, ExamType
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.ai.services.question_bank_service import ingest_from_paper
from app.modules.curriculum.schemas.concept_card import ConceptCardCreate
from app.modules.curriculum.services.concept_card_service import ConceptCardService
from app.modules.examinations.schemas.evaluation import EvaluationApprove
from app.modules.examinations.services.answer_sheet_eval_service import AnswerSheetEvalService
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.mastery.services.mastery_service import recompute_class_subject
from reference_school_config import (
    LOGIN_CLASS_INCHARGE,
    LOGIN_TEACHER_MATHS,
    SCHOOL_BOARD,
    TENANT_SLUG,
)

APPROVED_PAPER_TITLE = "Class 10 Maths — Quadratic Equations (Demo)"
PENDING_PAPER_TITLE = "Class 10 Maths — Progressions (Pending approval)"
DEMO_EXAM_TITLE = "Unit Test — Quadratic Equations"
QUADRATIC_TOPIC = "Quadratic Equations"
CLASS_WORK_NOTICE_TITLE = "Class work — Quadratic Equations practice"

DEMO_SECTIONS = [
    {
        "title": "Section A",
        "instructions": "Answer all questions.",
        "questions": [
            {
                "number": "1",
                "text": "Find the roots of x² − 5x + 6 = 0.",
                "marks": 2,
                "type": "short",
                "answer_key": "2 and 3",
                "topic": "Quadratic Equations",
            },
            {
                "number": "2",
                "text": "Which is the correct discriminant for 2x² + 3x + 5 = 0?",
                "marks": 1,
                "type": "mcq",
                "options": ["−31", "31", "0", "49"],
                "answer_key": "A",
                "topic": "Quadratic Equations",
            },
            {
                "number": "3",
                "text": "Explain the nature of roots when the discriminant is negative.",
                "marks": 3,
                "type": "long",
                "answer_key": "No real roots; roots are complex conjugates.",
                "topic": "Quadratic Equations",
            },
        ],
    },
]

# Sai Rao (student_demo) answers — Q2 wrong on purpose for demo eval story.
DEMO_STUDENT_ANSWERS = {
    "1": "x = 2, x = 3",
    "2": "B",
    "3": "When discriminant is negative there are no real roots.",
}

DEMO_AI_SUGGESTIONS = {
    "1": {
        "marks_suggested": 2.0,
        "max_marks": 2.0,
        "feedback": "Correct factorisation and both roots identified.",
        "confidence": 0.95,
        "student_answer": DEMO_STUDENT_ANSWERS["1"],
        "topic": "Quadratic Equations",
        "method": "objective",
        "criteria": [],
        "missing_concepts": [],
    },
    "2": {
        "marks_suggested": 0.0,
        "max_marks": 1.0,
        "feedback": "Incorrect. Discriminant b² − 4ac = 9 − 40 = −31 (option A).",
        "confidence": 0.98,
        "student_answer": DEMO_STUDENT_ANSWERS["2"],
        "topic": "Quadratic Equations",
        "method": "objective",
        "criteria": [],
        "missing_concepts": ["Discriminant"],
    },
    "3": {
        "marks_suggested": 1.0,
        "max_marks": 3.0,
        "feedback": "Partial credit — states no real roots but misses conjugate-pair detail.",
        "confidence": 0.82,
        "student_answer": DEMO_STUDENT_ANSWERS["3"],
        "topic": "Quadratic Equations",
        "method": "heuristic_fallback",
        "criteria": [
            {"criterion": "States no real roots", "marks_awarded": 1.5, "max_marks": 1.5},
            {"criterion": "Mentions complex/conjugate roots", "marks_awarded": 1.0, "max_marks": 1.5},
        ],
        "missing_concepts": [],
    },
}


async def _get_context(db):
    school = (
        await db.execute(select(School).where(School.tenant_slug == TENANT_SLUG))
    ).scalar_one_or_none()
    if not school:
        print(f"School not found (tenant={TENANT_SLUG}). Run seed_reference_school.py first.")
        return None

    cls = (
        await db.execute(
            select(Class).where(
                Class.school_id == school.id,
                Class.grade == "Class 10",
                Class.section == "A",
            )
        )
    ).scalar_one_or_none()
    maths = None
    if cls:
        maths = (
            await db.execute(
                select(Subject).where(
                    Subject.school_id == school.id,
                    Subject.class_id == cls.id,
                    Subject.name == "Mathematics",
                )
            )
        ).scalar_one_or_none()

    teacher6 = (
        await db.execute(
            select(User).where(User.school_id == school.id, User.username == LOGIN_TEACHER_MATHS)
        )
    ).scalar_one_or_none()
    incharge = (
        await db.execute(
            select(User).where(User.school_id == school.id, User.username == LOGIN_CLASS_INCHARGE)
        )
    ).scalar_one_or_none()

    pack = None
    if cls and maths:
        ay = (
            await db.execute(select(AcademicYear).where(AcademicYear.id == cls.academic_year_id))
        ).scalar_one_or_none()
        if ay:
            pack = (
                await db.execute(
                    select(CurriculumPack).where(
                        CurriculumPack.school_id == school.id,
                        CurriculumPack.class_id == cls.id,
                        CurriculumPack.subject_id == maths.id,
                        CurriculumPack.academic_year_id == ay.id,
                        CurriculumPack.status == PackStatus.APPROVED,
                    )
                )
            ).scalars().first()

    student = None
    if cls:
        student = (
            await db.execute(
                select(Student).where(
                    Student.school_id == school.id,
                    Student.class_id == cls.id,
                    Student.roll_no == "1",
                )
            )
        ).scalar_one_or_none()

    return {
        "school": school,
        "cls": cls,
        "maths": maths,
        "teacher6": teacher6,
        "incharge": incharge,
        "pack": pack,
        "student": student,
    }


async def _seed_approved_paper(ctx, db) -> QuestionPaper | None:
    school, cls, maths, teacher6, incharge, pack = (
        ctx["school"],
        ctx["cls"],
        ctx["maths"],
        ctx["teacher6"],
        ctx["incharge"],
        ctx["pack"],
    )
    if not all([cls, maths, teacher6, incharge]):
        print("  ! missing class/subject/teachers — skip question papers")
        return None

    existing = (
        await db.execute(
            select(QuestionPaper).where(
                QuestionPaper.school_id == school.id,
                QuestionPaper.title == APPROVED_PAPER_TITLE,
            )
        )
    ).scalar_one_or_none()
    if existing:
        print(f"  = approved paper already exists ({existing.id})")
        return existing

    now = datetime.now(timezone.utc)
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        created_by=teacher6.id,
        pack_id=pack.id if pack else None,
        grounded=bool(pack),
        grounding_sources=[
            {
                "index": 1,
                "chapter": "Quadratic Equations",
                "topic": "Standard form",
                "ref_id": "ch-5",
            }
        ]
        if pack
        else None,
        title=APPROVED_PAPER_TITLE,
        board=SCHOOL_BOARD,
        grade="Class 10",
        subject_name="Mathematics",
        total_marks=Decimal("6"),
        duration_minutes=45,
        topics=["Quadratic Equations"],
        sections=DEMO_SECTIONS,
        status=PaperStatus.APPROVED,
        ai_model="demo-seed",
        approved_by=incharge.id,
        approved_at=now,
        submitted_at=now,
    )
    db.add(paper)
    await db.flush()
    await ingest_from_paper(db, paper, approved_by=incharge.id, approved_at=now)
    print(f"  + approved grounded paper ({paper.id})")
    return paper


async def _seed_pending_paper(ctx, db) -> None:
    school, cls, maths, teacher6 = (
        ctx["school"],
        ctx["cls"],
        ctx["maths"],
        ctx["teacher6"],
    )
    if not all([cls, maths, teacher6]):
        return

    existing = (
        await db.execute(
            select(QuestionPaper).where(
                QuestionPaper.school_id == school.id,
                QuestionPaper.title == PENDING_PAPER_TITLE,
            )
        )
    ).scalar_one_or_none()
    if existing:
        print("  = pending-approval paper already exists")
        return

    db.add(
        QuestionPaper(
            school_id=school.id,
            class_id=cls.id,
            subject_id=maths.id,
            created_by=teacher6.id,
            title=PENDING_PAPER_TITLE,
            board=SCHOOL_BOARD,
            grade="Class 10",
            subject_name="Mathematics",
            total_marks=Decimal("10"),
            duration_minutes=60,
            topics=["Progressions"],
            sections=[
                {
                    "title": "Section A",
                    "instructions": "Answer any five.",
                    "questions": [
                        {
                            "number": "1",
                            "text": "Find the 10th term of the AP: 3, 7, 11, ...",
                            "marks": 2,
                            "type": "short",
                            "answer_key": "39",
                        }
                    ],
                }
            ],
            status=PaperStatus.PENDING_APPROVAL,
            ai_model="demo-seed",
            submitted_at=datetime.now(timezone.utc),
        )
    )
    print("  + pending-approval paper (principal queue signal)")


async def _seed_demo_exam_and_eval(ctx, db, paper: QuestionPaper) -> None:
    school, cls, maths, teacher6, student = (
        ctx["school"],
        ctx["cls"],
        ctx["maths"],
        ctx["teacher6"],
        ctx["student"],
    )
    if not all([cls, maths, teacher6, student]):
        print("  ! missing exam prerequisites — skip eval seed")
        return

    question_schema = [
        {"no": str(q["number"]), "max_marks": float(q["marks"]), "topic": q.get("topic", "Quadratic Equations")}
        for section in DEMO_SECTIONS
        for q in section["questions"]
    ]

    exam = (
        await db.execute(
            select(Exam).where(
                Exam.school_id == school.id,
                Exam.class_id == cls.id,
                Exam.subject_id == maths.id,
                Exam.title == DEMO_EXAM_TITLE,
            )
        )
    ).scalar_one_or_none()

    if exam is None:
        exam = Exam(
            school_id=school.id,
            class_id=cls.id,
            subject_id=maths.id,
            exam_type=ExamType.UNIT_TEST,
            title=DEMO_EXAM_TITLE,
            total_marks=Decimal("6"),
            date=date(2026, 10, 5),
            topic="Quadratic Equations",
            question_schema=question_schema,
            source_paper_id=paper.id,
            created_by=teacher6.id,
        )
        db.add(exam)
        await db.flush()
        print(f"  + demo unit test exam ({exam.id})")
    else:
        exam.source_paper_id = paper.id
        exam.question_schema = question_schema
        exam.topic = "Quadratic Equations"
        print(f"  = demo exam updated ({exam.id})")

    existing_eval = (
        await db.execute(
            select(AnswerSheetEvaluation).where(
                AnswerSheetEvaluation.school_id == school.id,
                AnswerSheetEvaluation.exam_id == exam.id,
                AnswerSheetEvaluation.student_id == student.id,
            )
        )
    ).scalar_one_or_none()

    if existing_eval:
        stale = existing_eval.ai_suggestions != DEMO_AI_SUGGESTIONS
        if existing_eval.status == EVAL_STATUS_APPROVED:
            if stale:
                existing_eval.status = EVAL_STATUS_SUGGESTED
                existing_eval.ai_suggestions = DEMO_AI_SUGGESTIONS
                existing_eval.input_answers = DEMO_STUDENT_ANSWERS
                existing_eval.approved_by = None
                existing_eval.approved_at = None
                existing_eval.correction_summary = (
                    "AI suggests 3/6 — review Q2 (discriminant) and Q3 (partial credit)."
                )
                print("  = eval reset to suggested (demo marks updated)")
            else:
                print("  = eval already approved")
                return
        elif existing_eval.status != EVAL_STATUS_SUGGESTED:
            existing_eval.status = EVAL_STATUS_SUGGESTED
            existing_eval.ai_suggestions = DEMO_AI_SUGGESTIONS
            existing_eval.input_answers = DEMO_STUDENT_ANSWERS
            existing_eval.correction_summary = (
                "AI suggests 3/6 — review Q2 (discriminant) and Q3 (partial credit)."
            )
            print("  = eval reset to suggested for demo")
        else:
            print("  = eval already in suggested state")
        return

    db.add(
        AnswerSheetEvaluation(
            school_id=school.id,
            exam_id=exam.id,
            student_id=student.id,
            created_by=teacher6.id,
            status=EVAL_STATUS_SUGGESTED,
            input_answers=DEMO_STUDENT_ANSWERS,
            ai_suggestions=DEMO_AI_SUGGESTIONS,
            correction_summary=(
                "AI suggests 3/6 — review Q2 (discriminant) and Q3 (partial credit)."
            ),
        )
    )
    print("  + AI answer-sheet eval (suggested) for student roll 1")


async def _seed_quadratic_concept_card(ctx, db) -> None:
    """Approved Concept Card on Quadratic Equations — tutor grounding (not template fallback)."""
    school, cls, maths, incharge = (
        ctx["school"],
        ctx["cls"],
        ctx["maths"],
        ctx["incharge"],
    )
    if not all([cls, maths, incharge]):
        print("  ! skip quadratic concept card — missing class/subject/incharge")
        return

    ay = (
        await db.execute(select(AcademicYear).where(AcademicYear.id == cls.academic_year_id))
    ).scalar_one_or_none()
    if not ay:
        return

    pack = (
        await db.execute(
            select(CurriculumPack).where(
                CurriculumPack.school_id == school.id,
                CurriculumPack.class_id == cls.id,
                CurriculumPack.subject_id == maths.id,
                CurriculumPack.academic_year_id == ay.id,
                CurriculumPack.status == PackStatus.APPROVED,
            )
        )
    ).scalar_one_or_none()
    if pack is None:
        print("  ! skip quadratic concept card — no approved maths pack")
        return

    concept = (
        await db.execute(
            select(CurriculumConcept)
            .join(CurriculumTopic, CurriculumTopic.id == CurriculumConcept.topic_id)
            .where(
                CurriculumConcept.school_id == school.id,
                CurriculumConcept.pack_id == pack.id,
                CurriculumTopic.title.ilike(f"%{QUADRATIC_TOPIC}%"),
                CurriculumConcept.slug == "quadratic-formula",
            )
        )
    ).scalar_one_or_none()

    if concept is None:
        concept = (
            await db.execute(
                select(CurriculumConcept)
                .join(CurriculumTopic, CurriculumTopic.id == CurriculumConcept.topic_id)
                .where(
                    CurriculumConcept.school_id == school.id,
                    CurriculumConcept.pack_id == pack.id,
                    CurriculumTopic.title.ilike(f"%{QUADRATIC_TOPIC}%"),
                )
                .order_by(CurriculumConcept.order_index)
            )
        ).scalars().first()

    if concept is None:
        await KnowledgeGraphService(db).build_spine_from_pack(
            school_id=school.id, pack_id=pack.id
        )
        concept = (
            await db.execute(
                select(CurriculumConcept)
                .join(CurriculumTopic, CurriculumTopic.id == CurriculumConcept.topic_id)
                .where(
                    CurriculumConcept.school_id == school.id,
                    CurriculumConcept.pack_id == pack.id,
                    CurriculumTopic.title.ilike(f"%{QUADRATIC_TOPIC}%"),
                    CurriculumConcept.slug == "quadratic-formula",
                )
            )
        ).scalar_one_or_none()
        if concept is None:
            concept = (
                await db.execute(
                    select(CurriculumConcept)
                    .join(CurriculumTopic, CurriculumTopic.id == CurriculumConcept.topic_id)
                    .where(
                        CurriculumConcept.school_id == school.id,
                        CurriculumConcept.pack_id == pack.id,
                        CurriculumTopic.title.ilike(f"%{QUADRATIC_TOPIC}%"),
                    )
                    .order_by(CurriculumConcept.order_index)
                )
            ).scalars().first()

    if concept is None:
        print("  ! skip quadratic concept card — no spine concept for Quadratic Equations")
        return

    existing = (
        await db.execute(
            select(ConceptCard).where(
                ConceptCard.school_id == school.id,
                ConceptCard.concept_id == concept.id,
            )
        )
    ).scalar_one_or_none()
    if existing and existing.status == ConceptCardStatus.APPROVED:
        print(f"  = quadratic concept card approved (slug={concept.slug})")
        return

    svc = ConceptCardService(db)
    if existing is None:
        card = await svc.create_card(
            school_id=school.id,
            concept_id=concept.id,
            data=ConceptCardCreate(
                title=f"{QUADRATIC_TOPIC} — discriminant and roots",
                explanation=(
                    "For a quadratic equation ax² + bx + c = 0, the discriminant "
                    "Δ = b² − 4ac tells you about the roots. When Δ > 0 there are two "
                    "distinct real roots; when Δ = 0 one repeated root; when Δ < 0 there "
                    "are no real roots (only complex conjugate pairs). Always substitute "
                    "roots back into the original equation to verify."
                ),
                examples=[
                    "2x² − 5x + 2 = 0 factors to (2x − 1)(x − 2) = 0, so x = ½ or 2.",
                    "For 2x² + 3x + 5 = 0, Δ = 9 − 40 = −31 — no real roots.",
                ],
                hints=[
                    "Write the equation in standard form ax² + bx + c = 0 first.",
                    "Compute b² − 4ac before choosing factorisation or the formula.",
                ],
                visual_kind="equation",
            ),
            created_by=incharge.id,
        )
    else:
        card = existing

    await svc.approve_card(
        school_id=school.id, card_id=card.id, approved_by=incharge.id
    )
    print(f"  + approved concept card for tutor (slug={concept.slug})")


async def _remove_legacy_fractions_misconceptions(ctx, db) -> None:
    """Drop pre-loop fractions seed so tutor uses exam-derived weak topics."""
    school, student = ctx["school"], ctx["student"]
    if not student:
        return
    rows = (
        await db.execute(
            select(MisconceptionEntry).where(
                MisconceptionEntry.school_id == school.id,
                MisconceptionEntry.student_id == student.id,
                MisconceptionEntry.topic.ilike("%fraction%"),
            )
        )
    ).scalars().all()
    for row in rows:
        await db.delete(row)
    if rows:
        print(f"  - removed {len(rows)} legacy fractions misconception(s)")


async def _finalize_demo_eval_and_mastery(ctx, db) -> None:
    """Approve AI eval → finalized marks → misconceptions → mastery recompute."""
    school, cls, maths, incharge, student = (
        ctx["school"],
        ctx["cls"],
        ctx["maths"],
        ctx["incharge"],
        ctx["student"],
    )
    if not all([cls, maths, incharge, student]):
        print("  ! skip eval finalization — missing class/subject/incharge/student")
        return

    exam = (
        await db.execute(
            select(Exam).where(
                Exam.school_id == school.id,
                Exam.class_id == cls.id,
                Exam.subject_id == maths.id,
                Exam.title == DEMO_EXAM_TITLE,
            )
        )
    ).scalar_one_or_none()
    if exam is None:
        return

    eval_row = (
        await db.execute(
            select(AnswerSheetEvaluation).where(
                AnswerSheetEvaluation.school_id == school.id,
                AnswerSheetEvaluation.exam_id == exam.id,
                AnswerSheetEvaluation.student_id == student.id,
            )
        )
    ).scalar_one_or_none()
    if eval_row is None:
        return

    if eval_row.status == EVAL_STATUS_SUGGESTED:
        svc = AnswerSheetEvalService(db)
        await svc.approve(
            school_id=school.id,
            evaluation_id=eval_row.id,
            data=EvaluationApprove(
                correction_summary=(
                    "Teacher approved AI marks — Q2 discriminant error noted for remediation."
                ),
            ),
            approved_by=incharge.id,
        )
        print("  + eval approved (marks finalized, misconceptions extracted)")
    elif eval_row.status == EVAL_STATUS_APPROVED:
        print("  = eval already finalized")
    else:
        print(f"  ! eval status={eval_row.status} — skip finalization")

    topic_rows = await recompute_class_subject(db, school.id, cls.id, maths.id)
    print(f"  + mastery recomputed ({topic_rows} topic rows)")


async def _seed_class_work_notice(ctx, db) -> None:
    school, cls, teacher6 = ctx["school"], ctx["cls"], ctx["teacher6"]
    if not cls or not teacher6:
        return

    existing = (
        await db.execute(
            select(Notice).where(
                Notice.school_id == school.id,
                Notice.title == CLASS_WORK_NOTICE_TITLE,
            )
        )
    ).scalar_one_or_none()
    if existing:
        print("  = class work notice already exists")
        return

    db.add(
        Notice(
            school_id=school.id,
            title=CLASS_WORK_NOTICE_TITLE,
            content=(
                "Complete Exercise 5.2 (Q1–Q8) from your textbook. "
                "Submit working for factorisation problems. "
                "Due: next Maths period (Wednesday)."
            ),
            audience=NoticeAudience.EXTERNAL,
            target_roles=["parent", "student"],
            priority=NoticePriority.MEDIUM,
            class_id=cls.id,
            created_by=teacher6.id,
        )
    )
    print("  + class work notice (parents + students)")


async def main() -> None:
    async with async_session_factory() as db:
        ctx = await _get_context(db)
        if not ctx or not ctx["school"]:
            return

        print("Seeding Demo v1 assets for Reference School…")
        paper = await _seed_approved_paper(ctx, db)
        await _seed_pending_paper(ctx, db)
        if paper:
            await _seed_quadratic_concept_card(ctx, db)
            await _seed_demo_exam_and_eval(ctx, db, paper)
            await _remove_legacy_fractions_misconceptions(ctx, db)
            await _finalize_demo_eval_and_mastery(ctx, db)
        await _seed_class_work_notice(ctx, db)
        await db.commit()
        print("Demo v1 seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
