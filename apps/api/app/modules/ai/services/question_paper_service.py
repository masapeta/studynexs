"""AI question-paper generation: blueprint + prompt -> LLM gateway -> parsed draft paper.

Board / grade / subject / blueprint are INPUTS (data), so the same code serves any board —
only the inputs change. The default blueprint here is an SSC-style structure; swap in a
board's official blueprint or a school-provided sample to match format exactly.
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.modules.ai.gateway import LLMMessage, default_model, get_provider, record_usage

logger = structlog.get_logger()

_DIFFICULTY_MIX = {
    "easy": {"easy": 60, "medium": 30, "hard": 10},
    "balanced": {"easy": 40, "medium": 40, "hard": 20},
    "hard": {"easy": 20, "medium": 40, "hard": 40},
}


def _ssc_blueprint(total_marks: int) -> list[dict]:
    """Authentic Telangana (TSBIE/BSE) SSC Class-10 paper structure — 80 marks.

    Modelled on real March-2024 SSC Maths papers: Part-A (Sections I-III, 60 marks) +
    Part-B objective (20 marks). `answer_any` marks an internal-choice section (print N,
    answer fewer). Non-standard totals fall back to a scaled version.
    """
    standard = [
        {"title": "Section I", "marks_per_q": 2, "count": 6, "type": "very_short",
         "instructions": "Answer ALL questions. Each question carries 2 marks."},
        {"title": "Section II", "marks_per_q": 4, "count": 6, "type": "short",
         "instructions": "Answer ALL questions. Each question carries 4 marks."},
        {"title": "Section III", "marks_per_q": 6, "count": 6, "answer_any": 4, "type": "long",
         "instructions": "Answer ANY FOUR of the following six questions. Each carries 6 marks."},
        {"title": "Part-B (Objective)", "marks_per_q": 1, "count": 20, "type": "mcq",
         "instructions": "Answer ALL. Each carries 1 mark; write the correct option (A/B/C/D)."},
    ]
    standard_total = sum(s["marks_per_q"] * s.get("answer_any", s["count"]) for s in standard)
    if total_marks in (0, standard_total):
        return standard
    factor = total_marks / standard_total
    return [{**s, "count": max(1, round(s["count"] * factor))} for s in standard]


def _build_messages(*, board, grade, subject, topics, total_marks, duration, difficulty, plan):
    mix = _DIFFICULTY_MIX.get(difficulty, _DIFFICULTY_MIX["balanced"])
    plan_lines = "\n".join(
        f"- {s['title']}: {s['count']} questions x {s['marks_per_q']} marks "
        f"({s['type']}). {s['instructions']}"
        for s in plan
    )
    topic_str = ", ".join(topics) if topics else "the full prescribed syllabus for this class"
    system = (
        f"You are an experienced {board} board examiner setting a {grade} {subject} "
        f"question paper for an Indian school. Produce an authentic, exam-ready paper. "
        f"Rules: stay STRICTLY within the given topics/syllabus — never include "
        f"out-of-syllabus content; no duplicate or near-duplicate questions; every "
        f"question must be clear, unambiguous and correctly solvable; follow the "
        f"section plan and marks exactly. Return JSON only."
    )
    user = (
        f"Create a {board} {grade} {subject} question paper.\n"
        f"Total marks: {total_marks}. Duration: {duration} minutes.\n"
        f"Topics to cover: {topic_str}.\n"
        f"Difficulty mix (approx %): easy {mix['easy']}, "
        f"medium {mix['medium']}, hard {mix['hard']}.\n"
        f"Follow EXACTLY this section plan:\n{plan_lines}\n\n"
        "Return JSON of this shape:\n"
        '{"title": str, "general_instructions": [str, ...], "sections": ['
        '{"title": str, "instructions": str, "questions": ['
        '{"number": str, "text": str, "marks": number, "type": str, '
        '"options": [str] (only for mcq), "answer_key": str}]}]}\n'
        "Every MCQ must have exactly 4 options. Provide a concise answer_key (a full worked "
        "solution for long questions) for EVERY question — these are for the teacher only."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _normalize_sections(raw_sections) -> list[dict]:
    out: list[dict] = []
    for s in raw_sections or []:
        questions = []
        for q in (s.get("questions") or []):
            item = {
                "number": str(q.get("number", "")),
                "text": str(q.get("text", "")),
                "marks": float(q.get("marks", 0) or 0),
                "type": str(q.get("type", "short")),
            }
            if q.get("options"):
                item["options"] = [str(o) for o in q["options"]]
            if q.get("answer_key") is not None:
                item["answer_key"] = str(q.get("answer_key"))
            questions.append(item)
        out.append({
            "title": str(s.get("title", "")),
            "instructions": str(s["instructions"]) if s.get("instructions") else None,
            "questions": questions,
        })
    return out


async def generate_paper(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    created_by: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    topics: list[str],
    total_marks: int,
    duration_minutes: int,
    difficulty: str,
    title: str | None = None,
) -> QuestionPaper:
    """Generate a DRAFT question paper via the LLM gateway. Teacher reviews/approves after."""
    cls = (
        await db.execute(select(Class).where(Class.id == class_id, Class.school_id == school_id))
    ).scalar_one_or_none()
    if cls is None:
        raise ValueError("Class not found")
    subject = (
        await db.execute(
            select(Subject).where(
                Subject.id == subject_id,
                Subject.school_id == school_id,
                Subject.class_id == class_id,
            )
        )
    ).scalar_one_or_none()
    if subject is None:
        raise ValueError("Subject not found for this class")

    from app.db.models.school import School

    school = (await db.execute(select(School).where(School.id == school_id))).scalar_one()
    board = school.board or "SSC"
    grade = cls.grade

    plan = _ssc_blueprint(total_marks)
    official_total = sum(s["marks_per_q"] * s.get("answer_any", s["count"]) for s in plan)
    messages = _build_messages(
        board=board, grade=grade, subject=subject.name, topics=topics,
        total_marks=total_marks, duration=duration_minutes, difficulty=difficulty, plan=plan,
    )

    provider = get_provider()
    model = default_model()
    result = await provider.generate(
        messages, model=model, json_mode=True, max_tokens=8000, temperature=0.4
    )
    await record_usage(
        db, feature="question_paper", result=result, school_id=school_id, created_by=created_by
    )

    try:
        data = json.loads(result.text)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("question_paper_parse_failed", error=str(exc), raw=(result.text or "")[:400])
        raise ValueError("The AI returned an unreadable paper. Please try generating again.")

    sections = _normalize_sections(data.get("sections", []))
    general_instructions = data.get("general_instructions")
    if isinstance(general_instructions, list):
        general_instructions = "\n".join(str(x) for x in general_instructions)

    computed_total = sum(
        float(q.get("marks", 0)) for s in sections for q in s.get("questions", [])
    )

    paper = QuestionPaper(
        school_id=school_id,
        class_id=class_id,
        subject_id=subject_id,
        created_by=created_by,
        title=title or data.get("title") or f"{subject.name} — {grade}",
        board=board,
        grade=grade,
        subject_name=subject.name,
        total_marks=Decimal(str(official_total)),
        duration_minutes=duration_minutes,
        topics=topics or None,
        difficulty_mix=_DIFFICULTY_MIX.get(difficulty, _DIFFICULTY_MIX["balanced"]),
        general_instructions=general_instructions,
        sections=sections,
        status=PaperStatus.DRAFT,
        ai_model=f"{result.provider}:{result.model}",
    )
    db.add(paper)
    await db.flush()
    logger.info(
        "question_paper_generated",
        paper_id=str(paper.id),
        marks=computed_total,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
    )
    return paper
