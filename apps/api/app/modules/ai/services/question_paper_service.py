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

from app.core.config import get_settings
from app.core.tenant_scope import TenantScope
from app.db.models.academic import Class, Subject
from app.db.models.ai_usage import AIUsage
from app.db.models.curriculum_pack import CurriculumChapter
from app.db.models.examination import ExamType
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.gateway import LLMMessage, LLMResult, generate_llm, record_usage
from app.modules.ai.gateway.input_guard import sanitize_prompt_text
from app.modules.ai.gateway.json_parse import LLMJsonError, parse_llm_json
from app.modules.ai.gateway.output_guard import sanitize_paper_sections
from app.modules.ai.question_paper_constraints import (
    QUESTION_OUTPUT_TOKEN_BUDGET,
    estimated_question_output_tokens,
)
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits
from app.modules.ai.services.question_bank_service import (
    compose_exact_sections_from_plan,
    compose_sections_from_plan,
    fetch_compose_candidates,
    merge_exact_gap_fill,
    merge_gap_fill,
    note_bank_items_used,
    renumber_sections,
)
from app.modules.ai.vectorstore.base import VectorStore
from app.modules.curriculum.services.curriculum_grounding import (
    CurriculumGrounding,
    ground_approved_pack,
)

logger = structlog.get_logger()

_CUSTOM_QUESTION_TYPES = {
    "mcq",
    "fill_blank",
    "match",
    "true_false",
    "very_short",
    "short",
    "long",
    "very_long",
}
_BLOOM_LEVELS = {"Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"}


def _canonical_bloom(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return {
        "remember": "Remember",
        "understand": "Understand",
        "apply": "Apply",
        "analyse": "Analyze",
        "analyze": "Analyze",
        "evaluate": "Evaluate",
        "create": "Create",
    }.get(normalized, str(value or "").strip())


def _stub_qp_json(*, title: str, plan: list[dict], exact_plan: bool = False) -> str:
    """Minimal valid paper JSON when LLM is unavailable (dev/test demo resilience — G1-03)."""
    sections = []
    stub_sections = plan if exact_plan else plan[:3]
    for section in stub_sections:
        planned_count = int(section.get("answer_any") or section.get("count") or 1)
        count = planned_count if exact_plan else min(2, planned_count)
        questions = []
        for i in range(count):
            q_type = section.get("type") or "short"
            questions.append({
                "number": str(i + 1),
                "text": (
                    f"[Demo draft] Sample {q_type} question — replace before use in exams."
                ),
                "marks": section.get("marks_per_q", 1),
                "type": q_type,
                "answer_key": "Teacher to verify against syllabus.",
                **({"options": ["A", "B", "C", "D"]} if q_type == "mcq" else {}),
            })
        sections.append({
            "title": section.get("title", "Section"),
            "instructions": section.get("instructions", ""),
            "questions": questions,
        })
    return json.dumps({
        "title": title,
        "general_instructions": [
            "Demo draft paper — generated without live AI. Approve only after teacher review.",
        ],
        "sections": sections,
    })


def _stub_exact_gap_json(gaps: list[dict]) -> str:
    return json.dumps({
        "fills": [
            {
                "section_index": gap["section_index"],
                "question_index": gap["question_index"],
                "text": "[Demo draft] Replace this question before use in exams.",
                "marks": gap["marks"],
                "type": gap["type"],
                "answer_key": "Teacher to verify against syllabus.",
                **(
                    {"options": ["A", "B", "C", "D"]}
                    if gap["type"] == "mcq"
                    else {}
                ),
            }
            for gap in gaps
        ]
    })


async def _generate_qp_llm(
    messages: list[LLMMessage],
    *,
    json_mode: bool,
    max_tokens: int,
    temperature: float,
    caller: str,
    stub_title: str,
    stub_plan: list[dict],
    exact_plan: bool = False,
    stub_text: str | None = None,
) -> LLMResult:
    """Call LLM gateway; in dev/test without fallback provider, return a demo-safe stub paper."""
    try:
        return await generate_llm(
            messages,
            json_mode=json_mode,
            max_tokens=max_tokens,
            temperature=temperature,
            feature="question_paper",
            caller=caller,
        )
    except Exception as exc:
        settings = get_settings()
        allow_stub = (
            (settings.is_development or settings.ENVIRONMENT == "testing")
            and not (settings.AI_FALLBACK_PROVIDER or "").strip()
        )
        if not allow_stub:
            raise
        logger.warning("question_paper_llm_failed_using_stub", caller=caller, error=str(exc))
        return LLMResult(
            text=stub_text or _stub_qp_json(
                title=stub_title, plan=stub_plan, exact_plan=exact_plan
            ),
            provider="stub",
            model="dev-stub",
            tokens_in=0,
            tokens_out=0,
            latency_ms=0,
        )


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


def _normalize_custom_plan(total_marks: int, section_plan: list[dict] | None) -> list[dict]:
    """Validate a direct service caller's exact plan and return prompt-safe internal specs."""
    if section_plan is None:
        return _ssc_blueprint(total_marks)
    if not isinstance(section_plan, list) or not 1 <= len(section_plan) <= 24:
        raise ValueError("section_plan must contain between 1 and 24 sections")

    normalized: list[dict] = []
    titles: set[str] = set()
    planned_total = Decimal("0")
    for raw in section_plan:
        if not isinstance(raw, dict):
            raise ValueError("Each section_plan entry must be an object")
        title = sanitize_prompt_text(
            str(raw.get("title") or ""), max_length=200, field_name="section title"
        )
        if not title:
            raise ValueError("Every section_plan entry requires a title")
        if title.casefold() in titles:
            raise ValueError("section_plan titles must be unique")
        titles.add(title.casefold())

        try:
            count = int(raw.get("count"))
            marks = Decimal(str(raw.get("marks_per_q")))
        except (TypeError, ValueError, ArithmeticError) as exc:
            raise ValueError("section_plan count and marks_per_q must be numeric") from exc
        if not 1 <= count <= 60:
            raise ValueError("section_plan count must be between 1 and 60")
        if marks <= 0 or marks > 100 or marks.as_tuple().exponent < -2:
            raise ValueError("section_plan marks_per_q must be 0.01 to 100 with at most 2 decimals")

        question_type = str(raw.get("type") or "").strip().lower()
        if question_type not in _CUSTOM_QUESTION_TYPES:
            raise ValueError(f"Unsupported section_plan question type: {question_type or 'blank'}")
        instructions = sanitize_prompt_text(
            raw.get("instructions"),
            max_length=2000,
            field_name="section instructions",
        ) or ""
        normalized.append({
            "title": title,
            "count": count,
            "marks_per_q": float(marks),
            "type": question_type,
            "instructions": instructions,
        })
        planned_total += Decimal(count) * marks

    if planned_total != Decimal(total_marks):
        raise ValueError(
            f"section_plan totals {planned_total:g} marks; expected {total_marks}"
        )
    if sum(int(section["count"]) for section in normalized) > 120:
        raise ValueError("section_plan may contain at most 120 questions")
    estimated_output = estimated_question_output_tokens(
        [(str(section["type"]), int(section["count"])) for section in normalized]
    )
    if estimated_output > QUESTION_OUTPUT_TOKEN_BUDGET:
        raise ValueError(
            "section_plan is too large for one reliable generation; reduce the number "
            "of questions or split the paper into fewer long-answer sections"
        )
    return normalized


def _normalize_blueprint_slots(
    plan: list[dict], blueprint_slots: list[dict] | None
) -> dict[tuple[int, int], dict]:
    if blueprint_slots is None:
        return {}
    if not isinstance(blueprint_slots, list):
        raise ValueError("blueprint_slots must be a list")

    expected = {
        (section_index, question_index)
        for section_index, section in enumerate(plan)
        for question_index in range(int(section["count"]))
    }
    slots: dict[tuple[int, int], dict] = {}
    for raw in blueprint_slots:
        if not isinstance(raw, dict):
            raise ValueError("Each blueprint slot must be an object")
        try:
            coordinate = (int(raw.get("section_index")), int(raw.get("question_index")))
        except (TypeError, ValueError) as exc:
            raise ValueError("Blueprint slot coordinates must be integers") from exc
        if coordinate in slots:
            raise ValueError("blueprint_slots contains duplicate question coordinates")
        chapter = sanitize_prompt_text(
            str(raw.get("chapter") or ""), max_length=200, field_name="blueprint chapter"
        )
        bloom = _canonical_bloom(raw.get("bloom"))
        if not chapter:
            raise ValueError("Every blueprint slot requires a chapter")
        if bloom not in _BLOOM_LEVELS:
            raise ValueError(f"Unsupported Bloom level: {bloom or 'blank'}")
        chapter_id = raw.get("chapter_id")
        if chapter_id is not None:
            try:
                chapter_id = uuid.UUID(str(chapter_id))
            except (TypeError, ValueError) as exc:
                raise ValueError("Blueprint chapter_id must be a UUID") from exc
        slots[coordinate] = {
            "chapter": chapter,
            "chapter_id": chapter_id,
            "bloom": bloom,
        }

    actual = set(slots)
    if actual != expected:
        raise ValueError(
            "blueprint_slots must cover every planned question exactly once "
            f"(missing={len(expected - actual)}, unexpected={len(actual - expected)})"
        )
    return slots


def _reject_unvalidated_blueprint_ids(
    slots: dict[tuple[int, int], dict],
) -> None:
    """Prevent ungrounded inputs from presenting caller IDs as curriculum authority.

    Stable chapter IDs are authoritative only after they have been resolved against the
    tenant-scoped approved CurriculumPack. Ungrounded and question-bank-only generation may
    still use chapter labels for matching, but must not persist unverified identifiers.
    """
    if any(slot.get("chapter_id") is not None for slot in slots.values()):
        raise ValueError("blueprint chapter_id requires an approved curriculum pack")


async def _validate_grounded_blueprint_chapters(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
    slots: dict[tuple[int, int], dict],
) -> None:
    """Bind every grounded slot to a real chapter in the approved tenant pack."""
    if not slots:
        return
    rows = (
        await db.execute(
            select(CurriculumChapter).where(
                CurriculumChapter.school_id == school_id,
                CurriculumChapter.pack_id == pack_id,
            )
        )
    ).scalars().all()
    by_id = {chapter.id: chapter for chapter in rows}
    by_label: dict[str, list[CurriculumChapter]] = {}
    for chapter in rows:
        label = f"{chapter.number}. {chapter.title}" if chapter.number else chapter.title
        by_label.setdefault(label.casefold(), []).append(chapter)

    for slot in slots.values():
        chapter: CurriculumChapter | None = None
        if slot.get("chapter_id") is not None:
            chapter = by_id.get(slot["chapter_id"])
            if chapter is None:
                raise ValueError(
                    "Blueprint chapter does not belong to the selected approved curriculum pack"
                )
        else:
            matches = by_label.get(str(slot["chapter"]).casefold(), [])
            if len(matches) != 1:
                raise ValueError(
                    "Grounded blueprint chapters require a unique curriculum chapter reference"
                )
            chapter = matches[0]
        canonical_label = (
            f"{chapter.number}. {chapter.title}" if chapter.number else chapter.title
        )
        slot["chapter_id"] = chapter.id
        slot["chapter"] = canonical_label


def _blueprint_prompt_lines(slots: dict[tuple[int, int], dict]) -> str:
    if not slots:
        return ""
    lines = [
        "Question blueprint (zero-based section/question coordinates; follow exactly):"
    ]
    for (section_index, question_index), slot in sorted(slots.items()):
        lines.append(
            f"- section {section_index}, question {question_index}: "
            f"chapter={slot['chapter']}; Bloom={slot['bloom']}"
        )
    return "\n".join(lines)


def _build_messages(
    *, board, grade, subject, exam_type, topics, total_marks, duration, difficulty, plan,
    blueprint_slots: dict[tuple[int, int], dict] | None = None,
):
    mix = _DIFFICULTY_MIX.get(difficulty, _DIFFICULTY_MIX["balanced"])
    plan_lines = "\n".join(
        f"- {s['title']}: {s['count']} questions x {s['marks_per_q']} marks "
        f"({s['type']}). {s['instructions']}"
        for s in plan
    )
    topic_str = ", ".join(topics) if topics else "the full prescribed syllabus for this class"
    blueprint_text = _blueprint_prompt_lines(blueprint_slots or {})
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
        f"Assessment type: {exam_type.value.replace('_', ' ')}.\n"
        f"Total marks: {total_marks}. Duration: {duration} minutes.\n"
        f"Topics to cover: {topic_str}.\n"
        f"Difficulty mix (approx %): easy {mix['easy']}, "
        f"medium {mix['medium']}, hard {mix['hard']}.\n"
        f"Follow EXACTLY this section plan:\n{plan_lines}\n\n"
        + (f"{blueprint_text}\n\n" if blueprint_text else "")
        +
        "Return JSON of this shape:\n"
        '{"title": str, "general_instructions": [str, ...], "sections": ['
        '{"title": str, "instructions": str, "questions": ['
        '{"number": str, "text": str, "marks": number, "type": str, '
        '"options": [str] (only for mcq), "answer_key": str, '
        '"chapter": str (when a question blueprint is provided), '
        '"bloom": str (when a question blueprint is provided)}]}]}\n'
        "Every MCQ must have exactly 4 options. Provide a concise answer_key (a full worked "
        "solution for long questions) for EVERY question — these are for the teacher only."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _build_grounded_messages(
    *, board, grade, subject, exam_type, topics, total_marks, duration, difficulty, plan,
    context_text, source_count, blueprint_slots: dict[tuple[int, int], dict] | None = None,
):
    """Curriculum-aware prompt: the model may use ONLY the retrieved context and must cite it.

    This is the difference between Assessment Intelligence and a generic LLM paper — every
    question is tied to the school's approved curriculum and carries a traceable citation, a
    Bloom's level, a difficulty label, and the learning outcome it assesses (CLAUDE.md §40, §109).
    """
    mix = _DIFFICULTY_MIX.get(difficulty, _DIFFICULTY_MIX["balanced"])
    plan_lines = "\n".join(
        f"- {s['title']}: {s['count']} questions x {s['marks_per_q']} marks "
        f"({s['type']}). {s['instructions']}"
        for s in plan
    )
    topic_str = (
        ", ".join(topics) if topics else "the topics present in the curriculum context below"
    )
    blueprint_text = _blueprint_prompt_lines(blueprint_slots or {})
    system = (
        f"You are an experienced {board} board examiner setting a {grade} {subject} question "
        f"paper for an Indian school. You MUST base every question ONLY on the CURRICULUM CONTEXT "
        f"provided below — never use outside knowledge and never introduce out-of-syllabus "
        f"content. For EVERY question you must: (1) cite the context source number(s) it is drawn "
        f'from in a "citations" array; (2) classify its Bloom\'s level; (3) label its difficulty; '
        f"(4) state the learning outcome it assesses. No duplicate or near-duplicate questions; "
        f"every question must be clear, unambiguous and correctly solvable; follow the section "
        f"plan and marks exactly. Return JSON only."
    )
    user = (
        f"CURRICULUM CONTEXT (numbered sources 1..{source_count} — cite these by number):\n"
        f"{context_text}\n\n"
        f"Create a {board} {grade} {subject} question paper grounded ONLY in the context above.\n"
        f"Assessment type: {exam_type.value.replace('_', ' ')}.\n"
        f"Total marks: {total_marks}. Duration: {duration} minutes.\n"
        f"Focus topics: {topic_str}.\n"
        f"Difficulty mix (approx %): easy {mix['easy']}, "
        f"medium {mix['medium']}, hard {mix['hard']}.\n"
        f"Follow EXACTLY this section plan:\n{plan_lines}\n\n"
        + (f"{blueprint_text}\n\n" if blueprint_text else "")
        +
        "Return JSON of this shape:\n"
        '{"title": str, "general_instructions": [str, ...], "sections": ['
        '{"title": str, "instructions": str, "questions": ['
        '{"number": str, "text": str, "marks": number, "type": str, '
        '"options": [str] (only for mcq), "answer_key": str, "chapter": str, '
        '"bloom": str (one of: Remember, Understand, Apply, Analyze, Evaluate, Create), '
        '"difficulty": str (easy | medium | hard), "learning_outcome": str, '
        '"concepts": [str], '
        f'"citations": [int] (source numbers from 1 to {source_count} above)}}]}}]}}\n'
        "Every MCQ must have exactly 4 options. Provide a concise answer_key (a full worked "
        "solution for long questions) for EVERY question — these are for the teacher only. "
        "Every question MUST include at least one valid citation to the curriculum context."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _build_gap_fill_messages(
    *,
    board: str,
    grade: str,
    subject: str,
    exam_type: ExamType,
    topics: list[str],
    gaps: list[dict],
    blueprint_slots: dict[tuple[int, int], dict] | None = None,
) -> list[LLMMessage]:
    exact_gaps = bool(gaps) and all("section_index" in gap for gap in gaps)
    if exact_gaps:
        gap_lines = "\n".join(
            f"- section {g['section_index']}, question {g['question_index']}: "
            f"{g['marks']} marks ({g['type']}), chapter={g['chapter']}, "
            f"Bloom={g['bloom']}"
            for g in gaps
        )
    else:
        gap_lines = "\n".join(
            f"- {g['section_title']}: {g['count']} x {g['marks']} marks ({g['type']})"
            for g in gaps
        )
    topic_str = ", ".join(topics) if topics else "the prescribed syllabus"
    blueprint_text = _blueprint_prompt_lines(blueprint_slots or {})
    system = (
        f"You are an experienced {board} board examiner. Generate ONLY the missing "
        f"questions listed below — do not repeat or rephrase provided bank content. "
        f"Return JSON only."
    )
    exact_contract = (
        'Return JSON: {"fills": [{"section_index": int, "question_index": int, '
        '"text": str, "marks": number, "type": str, "options": [str] (mcq only), '
        '"answer_key": str}]}\n'
    )
    legacy_contract = (
        'Return JSON: {"fills": [{"section_title": str, "questions": ['
        '{"number": str, "text": str, "marks": number, "type": str, '
        '"options": [str] (mcq only), "answer_key": str}]}]}\n'
    )
    user = (
        f"Class: {grade}. Subject: {subject}. "
        f"Assessment type: {exam_type.value.replace('_', ' ')}. Topics: {topic_str}.\n"
        f"Generate these missing questions only:\n{gap_lines}\n\n"
        + (
            f"Use this teacher blueprint when choosing content:\n{blueprint_text}\n\n"
            if blueprint_text
            else ""
        )
        + (exact_contract if exact_gaps else legacy_contract)
        + "Every MCQ needs exactly 4 options and an answer_key for every question."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def normalize_sections(raw_sections) -> list[dict]:
    return sanitize_paper_sections(raw_sections or [])


def validate_exact_sections(
    raw_sections: object,
    *,
    plan: list[dict],
    blueprint_slots: dict[tuple[int, int], dict] | None = None,
) -> list[dict]:
    """Fail closed when AI/bank output drifts from a teacher's exact plan.

    Section labels and numbering are teacher-authoritative, so those are normalized from the
    plan. Generated academic content, marks, types, options, and answers are validated rather
    than silently repaired. Chapter/Bloom values come from the teacher's blueprint, never the
    model, and are applied only after the generated shape has passed validation.
    """
    sections = normalize_sections(raw_sections)
    if len(sections) != len(plan):
        raise ValueError(
            f"Generated paper has {len(sections)} sections; expected {len(plan)}. Please retry."
        )

    slot_map = blueprint_slots or {}
    out: list[dict] = []
    question_number = 1
    computed_total = Decimal("0")
    for section_index, spec in enumerate(plan):
        section = sections[section_index]
        questions = list(section.get("questions") or [])
        expected_count = int(spec["count"])
        if len(questions) != expected_count:
            raise ValueError(
                f"Generated section '{spec['title']}' has {len(questions)} questions; "
                f"expected {expected_count}. Please retry."
            )

        expected_marks = Decimal(str(spec["marks_per_q"]))
        expected_type = str(spec["type"])
        exact_questions: list[dict] = []
        for question_index, question in enumerate(questions):
            text = str(question.get("text") or "").strip()
            answer_key = str(question.get("answer_key") or "").strip()
            if not text:
                raise ValueError(
                    f"Generated question {question_number} is blank. Please retry."
                )
            if not answer_key:
                raise ValueError(
                    f"Generated question {question_number} has no answer key. Please retry."
                )

            actual_marks = Decimal(str(question.get("marks", 0)))
            if actual_marks != expected_marks:
                raise ValueError(
                    f"Generated question {question_number} carries {actual_marks:g} marks; "
                    f"expected {expected_marks:g}. Please retry."
                )
            actual_type = str(question.get("type") or "").strip().lower()
            if actual_type != expected_type:
                raise ValueError(
                    f"Generated question {question_number} is type '{actual_type or 'blank'}'; "
                    f"expected '{expected_type}'. Please retry."
                )

            options = question.get("options")
            if expected_type == "mcq":
                if (
                    not isinstance(options, list)
                    or len(options) != 4
                    or any(not str(option).strip() for option in options)
                ):
                    raise ValueError(
                        f"Generated MCQ {question_number} must have exactly four non-blank "
                        "options. Please retry."
                    )

            exact_question = dict(question)
            exact_question["number"] = str(question_number)
            slot = slot_map.get((section_index, question_index))
            if slot:
                exact_question["chapter"] = slot["chapter"]
                if slot.get("chapter_id") is not None:
                    exact_question["chapter_id"] = str(slot["chapter_id"])
                exact_question["bloom"] = slot["bloom"]
            exact_questions.append(exact_question)
            question_number += 1
            computed_total += actual_marks

        out.append({
            "title": spec["title"],
            "instructions": spec.get("instructions") or None,
            "questions": exact_questions,
        })

    expected_total = sum(
        Decimal(int(spec["count"])) * Decimal(str(spec["marks_per_q"])) for spec in plan
    )
    if computed_total != expected_total:
        raise ValueError(
            f"Generated paper totals {computed_total:g} marks; expected {expected_total:g}. "
            "Please retry."
        )
    return out


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
    exam_type: ExamType = ExamType.UNIT_TEST,
    title: str | None = None,
    ungrounded_reason: str | None = None,
    role: str = "teacher",
    purpose_tag: str = "qp_full",
    credits_charged: int | None = None,
    pack_id: uuid.UUID | None = None,
    embedder: EmbeddingService | None = None,
    store: VectorStore | None = None,
    section_plan: list[dict] | None = None,
    blueprint_slots: list[dict] | None = None,
) -> QuestionPaper:
    """Generate a DRAFT question paper via the LLM gateway. Teacher reviews/approves after.

    When ``pack_id`` is given, generation is grounded in that APPROVED CurriculumPack: the paper
    is built ONLY from curriculum context retrieved through the shared RAG platform, and every
    question carries a citation back to it (Assessment Intelligence). ``embedder``/``store`` are
    injectable for tests; production uses the configured shared services.
    """
    custom_plan = section_plan is not None
    if not custom_plan and blueprint_slots is not None:
        raise ValueError("blueprint_slots requires section_plan")
    plan = _normalize_custom_plan(total_marks, section_plan)
    slot_map = _normalize_blueprint_slots(plan, blueprint_slots)

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

    official_total = sum(s["marks_per_q"] * s.get("answer_any", s["count"]) for s in plan)

    # Curriculum grounding (Assessment Intelligence). Validate + retrieve BEFORE reserving QP
    # credits so a bad/empty pack fails fast without charging the teacher. All retrieval goes
    # through the shared RAG platform — the service never touches a provider/embedder directly.
    grounded = False
    grounding: CurriculumGrounding | None = None
    grounding_pack_id: uuid.UUID | None = None
    if pack_id is not None:
        grounding = await ground_approved_pack(
            db,
            school_id=school_id,
            pack_id=pack_id,
            class_id=class_id,
            subject_id=subject_id,
            topics=topics,
            embedder=embedder,
            store=store,
        )
        if grounding.is_empty:
            raise ValueError(
                "This curriculum pack has no chapters/topics to ground on yet. "
                "Add curriculum content, then generate."
            )
        await _validate_grounded_blueprint_chapters(
            db,
            school_id=school_id,
            pack_id=grounding.pack_id,
            slots=slot_map,
        )
        grounded = True
        grounding_pack_id = grounding.pack_id
        board = grounding.board or board
        messages = _build_grounded_messages(
            board=board, grade=grade, subject=subject.name, exam_type=exam_type, topics=topics,
            total_marks=total_marks, duration=duration_minutes, difficulty=difficulty,
            plan=plan, context_text=grounding.context_text, source_count=grounding.chunk_count,
            blueprint_slots=slot_map,
        )
    else:
        _reject_unvalidated_blueprint_ids(slot_map)
        messages = _build_messages(
            board=board, grade=grade, subject=subject.name, exam_type=exam_type, topics=topics,
            total_marks=total_marks, duration=duration_minutes, difficulty=difficulty, plan=plan,
            blueprint_slots=slot_map,
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

    result = await _generate_qp_llm(
        messages,
        json_mode=True,
        max_tokens=8000,
        temperature=0.4,
        caller="generate_paper",
        stub_title=title or f"{subject.name} — {grade}",
        stub_plan=plan,
        exact_plan=custom_plan,
    )
    usage_row = await _record_qp_llm_usage(
        db,
        result=result,
        reserved_row=reserved,
    ) if reserved else None

    try:
        data = parse_llm_json(result.text, feature="question_paper")
    except LLMJsonError as exc:
        raise ValueError(
            "The AI returned an unreadable paper. Please try generating again."
        ) from exc

    sections = (
        validate_exact_sections(data.get("sections", []), plan=plan, blueprint_slots=slot_map)
        if custom_plan
        else normalize_sections(data.get("sections", []))
    )
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
        exam_type=exam_type,
        total_marks=Decimal(str(official_total)),
        duration_minutes=duration_minutes,
        topics=topics or None,
        difficulty_mix=_DIFFICULTY_MIX.get(difficulty, _DIFFICULTY_MIX["balanced"]),
        general_instructions=general_instructions,
        sections=sections,
        status=PaperStatus.DRAFT,
        ai_model=f"{result.provider}:{result.model}",
        pack_id=grounding_pack_id,
        grounded=grounded,
        grounding_sources=(grounding.sources if grounding else None),
        ungrounded_reason=(ungrounded_reason if not grounded else None),
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
        grounded=grounded,
        grounding_sources=(grounding.chunk_count if grounding else 0),
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
    exam_type: ExamType = ExamType.UNIT_TEST,
    title: str | None = None,
    role: str = "teacher",
    purpose_tag: str = "qp_from_bank",
    credits_charged: int | None = None,
    section_plan: list[dict] | None = None,
    blueprint_slots: list[dict] | None = None,
) -> QuestionPaper:
    """Compose a draft paper from the school question bank; LLM fills only missing slots."""
    custom_plan = section_plan is not None
    if not custom_plan and blueprint_slots is not None:
        raise ValueError("blueprint_slots requires section_plan")
    plan = _normalize_custom_plan(total_marks, section_plan)
    slot_map = _normalize_blueprint_slots(plan, blueprint_slots)
    _reject_unvalidated_blueprint_ids(slot_map)

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

    official_total = sum(s["marks_per_q"] * s.get("answer_any", s["count"]) for s in plan)
    exact_bank_blueprint = custom_plan and bool(slot_map)
    if exact_bank_blueprint:
        sections, used_item_ids, gaps = compose_exact_sections_from_plan(
            plan, candidates, slot_map
        )
    else:
        sections, used_item_ids, gaps = compose_sections_from_plan(
            plan, candidates, normalize_to_plan=custom_plan
        )

    # The Studio advertises approved-question reuse, not hidden ungrounded generation. Fail
    # closed before reserving credits when its exact blueprint cannot be filled from approved
    # bank items. The legacy non-Studio compose path retains its established gap-fill behavior.
    if custom_plan and gaps:
        raise ValueError(
            "The approved question bank does not contain enough exact matches for this "
            "blueprint. Adjust the template or use full AI with an approved curriculum pack."
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

    llm_result: LLMResult | None = None
    fills: list[dict] = []
    if gaps:
        messages = _build_gap_fill_messages(
            board=board,
            grade=grade,
            subject=subject.name,
            exam_type=exam_type,
            topics=topics,
            gaps=gaps,
            blueprint_slots=slot_map,
        )
        llm_result = await _generate_qp_llm(
            messages,
            json_mode=True,
            max_tokens=4000,
            temperature=0.4,
            caller="generate_paper_from_bank",
            stub_title=title or f"{subject.name} — {grade} (from bank)",
            stub_plan=plan,
            exact_plan=custom_plan,
            stub_text=_stub_exact_gap_json(gaps) if exact_bank_blueprint else None,
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
        fills = fill_data.get("fills") or []
        if not isinstance(fills, list):
            raise ValueError("AI gap fills must be a list")

    if exact_bank_blueprint:
        sections = merge_exact_gap_fill(
            sections,
            fills,
            plan=plan,
            gaps=gaps,
        )
    elif gaps:
        sections = merge_gap_fill(sections, fills)

    sections = (
        validate_exact_sections(sections, plan=plan, blueprint_slots=slot_map)
        if custom_plan
        else renumber_sections(normalize_sections(sections))
    )
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
        exam_type=exam_type,
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
        gaps_filled=sum(int(gap.get("count", 1)) for gap in gaps),
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
        exam_type=getattr(source, "exam_type", ExamType.UNIT_TEST),
        total_marks=source.total_marks,
        duration_minutes=source.duration_minutes,
        topics=copy.deepcopy(source.topics),
        difficulty_mix=copy.deepcopy(source.difficulty_mix),
        general_instructions=source.general_instructions,
        # deep copy so editing the clone's questions can never mutate the source paper
        sections=copy.deepcopy(source.sections),
        status=PaperStatus.DRAFT,
        ai_model=source.ai_model,  # provenance of the original draft; the copy itself is free
        pack_id=(source.pack_id if class_id is None and subject_id is None else None),
        grounded=(bool(source.grounded) if class_id is None and subject_id is None else False),
        grounding_sources=(
            copy.deepcopy(source.grounding_sources)
            if class_id is None and subject_id is None
            else None
        ),
        ungrounded_reason=(
            source.ungrounded_reason
            if class_id is None and subject_id is None
            else "Retargeted duplicate requires curriculum and approval review."
        ),
    )
    db.add(clone)
    await db.flush()
    logger.info(
        "question_paper_duplicated",
        source_id=str(source.id), clone_id=str(clone.id), retargeted=class_id is not None,
    )
    return clone
