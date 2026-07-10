"""AI question-paper generation: blueprint + prompt -> LLM gateway -> parsed draft paper.

Board / grade / subject / blueprint are INPUTS (data), so the same code serves any board —
only the inputs change. The default blueprint here is an SSC-style structure; swap in a
board's official blueprint or a school-provided sample to match format exactly.
"""
from __future__ import annotations

import copy
import json
import uuid
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.academic import Class, Subject
from app.db.models.ai_usage import AIUsage
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.modules.ai.gateway import LLMMessage, LLMResult, generate_llm, record_usage
from app.modules.ai.gateway.output_guard import sanitize_paper_sections
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits
from app.modules.ai.services.question_bank_service import (
    compose_sections_from_plan,
    fetch_compose_candidates,
    merge_gap_fill,
    note_bank_items_used,
    renumber_sections,
)

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


def _build_gap_fill_messages(
    *,
    board: str,
    grade: str,
    subject: str,
    topics: list[str],
    gaps: list[dict],
) -> list[LLMMessage]:
    gap_lines = "\n".join(
        f"- {g['section_title']}: {g['count']} x {g['marks']} marks ({g['type']})"
        for g in gaps
    )
    topic_str = ", ".join(topics) if topics else "the prescribed syllabus"
    system = (
        f"You are an experienced {board} board examiner. Generate ONLY the missing "
        f"questions listed below — do not repeat or rephrase provided bank content. "
        f"Return JSON only."
    )
    user = (
        f"Class: {grade}. Subject: {subject}. Topics: {topic_str}.\n"
        f"Generate these missing questions only:\n{gap_lines}\n\n"
        'Return JSON: {"fills": [{"section_title": str, "questions": ['
        '{"number": str, "text": str, "marks": number, "type": str, '
        '"options": [str] (mcq only), "answer_key": str}]}]}\n'
        "Every MCQ needs exactly 4 options and an answer_key for every question."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def normalize_sections(raw_sections) -> list[dict]:
    return sanitize_paper_sections(raw_sections or [])


async def _record_qp_llm_usage(
    db: AsyncSession,
    *,
    result: LLMResult,
    reserved_row: AIUsage,
    ref_id: uuid.UUID | None = None,
) -> AIUsage:
    """Finalize a reserved row as soon as the provider returns."""
    return await record_usage(
        db,
        feature="question_paper",
        result=result,
        reserved_row=reserved_row,
        ref_type="question_paper",
        ref_id=ref_id,
    )


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
    role: str = "teacher",
    purpose_tag: str = "qp_full",
    credits_charged: int | None = None,
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

    cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
    reserved: AIUsage | None = None
    if cost > 0:
        reserved = await reserve_ai_credits(
            db,
            school_id,
            user_id=created_by,
            role=role,
            purpose_tag=purpose_tag,
            feature="question_paper",
            credits=cost,
            ref_type="question_paper",
        )

    result = await generate_llm(
        messages, json_mode=True, max_tokens=8000, temperature=0.4,
        feature="question_paper", caller="generate_paper",
    )
    usage_row = await _record_qp_llm_usage(
        db,
        result=result,
        reserved_row=reserved,
    ) if reserved else None

    try:
        data = json.loads(result.text)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("question_paper_parse_failed", error=str(exc), raw=(result.text or "")[:400])
        raise ValueError("The AI returned an unreadable paper. Please try generating again.")

    sections = normalize_sections(data.get("sections", []))
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
    if usage_row is not None:
        usage_row.ref_id = paper.id
        await db.flush()

    logger.info(
        "question_paper_generated",
        paper_id=str(paper.id),
        marks=computed_total,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
    )
    return paper


async def generate_paper_from_bank(
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
    role: str = "teacher",
    purpose_tag: str = "qp_from_bank",
    credits_charged: int | None = None,
) -> QuestionPaper:
    """Compose a draft paper from the school question bank; LLM fills only missing slots."""
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

    candidates = await fetch_compose_candidates(
        db,
        school_id=school_id,
        class_id=class_id,
        subject_id=subject_id,
        topics=topics,
    )
    if not candidates:
        raise ValueError(
            "No approved questions in the bank for this class and subject. "
            "Approve a paper first or use full AI generate."
        )

    plan = _ssc_blueprint(total_marks)
    official_total = sum(s["marks_per_q"] * s.get("answer_any", s["count"]) for s in plan)
    sections, used_item_ids, gaps = compose_sections_from_plan(plan, candidates)

    cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
    reserved: AIUsage | None = None
    if cost > 0:
        reserved = await reserve_ai_credits(
            db,
            school_id,
            user_id=created_by,
            role=role,
            purpose_tag=purpose_tag,
            feature="question_paper",
            credits=cost,
            ref_type="question_paper",
        )

    llm_result: LLMResult | None = None
    if gaps:
        messages = _build_gap_fill_messages(
            board=board,
            grade=grade,
            subject=subject.name,
            topics=topics,
            gaps=gaps,
        )
        llm_result = await generate_llm(
            messages, json_mode=True, max_tokens=4000, temperature=0.4,
            feature="question_paper", caller="generate_paper_from_bank",
        )
        if reserved:
            await _record_qp_llm_usage(db, result=llm_result, reserved_row=reserved)
        try:
            fill_data = json.loads(llm_result.text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("bank_gap_fill_parse_failed", error=str(exc))
            raise ValueError(
                "Could not fill missing questions from the bank. Please try again."
            ) from exc
        sections = merge_gap_fill(sections, fill_data.get("fills") or [])

    sections = renumber_sections(normalize_sections(sections))
    if not any(q for s in sections for q in s.get("questions") or []):
        raise ValueError("Could not compose a paper from the bank — not enough matching questions.")

    paper = QuestionPaper(
        school_id=school_id,
        class_id=class_id,
        subject_id=subject_id,
        created_by=created_by,
        title=title or f"{subject.name} — {grade} (from bank)",
        board=board,
        grade=grade,
        subject_name=subject.name,
        total_marks=Decimal(str(official_total)),
        duration_minutes=duration_minutes,
        topics=topics or None,
        difficulty_mix=_DIFFICULTY_MIX.get(difficulty, _DIFFICULTY_MIX["balanced"]),
        general_instructions=None,
        sections=sections,
        status=PaperStatus.DRAFT,
        ai_model=(
            f"{llm_result.provider}:{llm_result.model}"
            if llm_result
            else "bank:compose"
        ),
    )
    db.add(paper)
    await db.flush()
    await note_bank_items_used(db, used_item_ids, paper.id)

    if reserved is not None and not gaps:
        usage_result = LLMResult(
            text="", provider="bank", model="compose", tokens_in=0, tokens_out=0
        )
        await record_usage(
            db,
            feature="question_paper",
            result=usage_result,
            reserved_row=reserved,
            ref_type="question_paper",
            ref_id=paper.id,
        )
    elif reserved is not None and gaps:
        reserved.ref_id = paper.id
        await db.flush()
    logger.info(
        "question_paper_from_bank",
        paper_id=str(paper.id),
        bank_items=len(used_item_ids),
        gaps_filled=sum(g["count"] for g in gaps),
    )
    return paper


async def duplicate_paper(
    db: AsyncSession,
    *,
    source: QuestionPaper,
    created_by: uuid.UUID,
    title: str | None = None,
    class_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
) -> QuestionPaper:
    """Clone a paper into a fresh editable DRAFT owned by ``created_by``.

    Zero LLM, so it records NO AIUsage — a duplicate must not inflate the "papers generated /
    teacher-hours saved" number the /usage dashboard reports. A copy of an APPROVED paper
    re-enters review as a DRAFT (you can't inherit another teacher's sign-off).

    Optionally re-targets to another class. Subjects are class-scoped, so changing ``class_id``
    requires ``subject_id``; both are validated in-school (and subject-in-class) and the
    grade/subject_name snapshots are refreshed so the clone stays self-consistent.
    """
    school_id = source.school_id
    new_class_id, new_subject_id = source.class_id, source.subject_id
    grade, subject_name = source.grade, source.subject_name

    if class_id is not None:
        if subject_id is None:
            raise ValueError("subject_id is required when changing class_id")
        scope = TenantScope(db, school_id)
        cls = await scope.school_class(class_id)
        subject = await scope.subject_in_class(subject_id, class_id)
        new_class_id, new_subject_id = class_id, subject_id
        grade, subject_name = cls.grade, subject.name
    elif subject_id is not None:
        subject = await TenantScope(db, school_id).subject_in_class(subject_id, source.class_id)
        new_subject_id = subject_id
        subject_name = subject.name

    clone = QuestionPaper(
        school_id=school_id,
        class_id=new_class_id,
        subject_id=new_subject_id,
        created_by=created_by,
        title=title or f"{source.title} (Copy)",
        board=source.board,
        grade=grade,
        subject_name=subject_name,
        total_marks=source.total_marks,
        duration_minutes=source.duration_minutes,
        topics=copy.deepcopy(source.topics),
        difficulty_mix=copy.deepcopy(source.difficulty_mix),
        general_instructions=source.general_instructions,
        # deep copy so editing the clone's questions can never mutate the source paper
        sections=copy.deepcopy(source.sections),
        status=PaperStatus.DRAFT,
        ai_model=source.ai_model,  # provenance of the original draft; the copy itself is free
    )
    db.add(clone)
    await db.flush()
    logger.info(
        "question_paper_duplicated",
        source_id=str(source.id), clone_id=str(clone.id), retargeted=class_id is not None,
    )
    return clone
