"""Ingest approved question papers into the school-private question bank."""
from __future__ import annotations

import hashlib
import re
import uuid

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.question_bank import (
    BANK_STATUS_APPROVED,
    QuestionBankItem,
    QuestionSource,
    RubricBankItem,
)
from app.db.models.question_paper import QuestionPaper

logger = structlog.get_logger()

_WHITESPACE = re.compile(r"\s+")


class BankIngestError(ValueError):
    """Paper cannot be ingested into the question bank."""


def content_fingerprint(*, question_text: str, marks: float, question_type: str) -> str:
    """Stable hash for similarity / dedup within a school+subject scope."""
    normalized = _WHITESPACE.sub(" ", question_text.strip().lower())
    payload = f"{normalized}|{marks:.2f}|{question_type.lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_source(paper: QuestionPaper) -> QuestionSource:
    if paper.ai_model:
        return QuestionSource.AI
    return QuestionSource.TEACHER


def _question_number(question: dict, position: int) -> str:
    number = str(question.get("number") or "").strip()
    return number if number else str(position)


async def ingest_from_paper(
    db: AsyncSession,
    paper: QuestionPaper,
    *,
    approved_by: uuid.UUID,
    approved_at,
) -> list[QuestionBankItem]:
    """Replace bank rows for this paper with fresh items from its sections.

    Idempotent on re-approve: deletes prior items for ``source_paper_id`` then re-ingests.
    Raises ``BankIngestError`` when the paper has no ingestible questions.
    """
    from app.modules.ai.services.question_paper_service import normalize_sections
    from app.modules.knowledge_graph.services.question_concept_link_service import (
        QuestionConceptLinkService,
    )

    linker = QuestionConceptLinkService(db)
    await linker.delete_links_for_paper(school_id=paper.school_id, paper_id=paper.id)

    await db.execute(
        delete(QuestionBankItem).where(
            QuestionBankItem.source_paper_id == paper.id,
            QuestionBankItem.school_id == paper.school_id,
        )
    )

    sections = normalize_sections(paper.sections)
    if not sections:
        raise BankIngestError("Paper has no sections to add to the question bank")

    source = _resolve_source(paper)
    paper_id_str = str(paper.id)
    items: list[QuestionBankItem] = []
    pending_rubrics: list[tuple[QuestionBankItem, str]] = []
    questions_by_key: dict[tuple[str, str], dict] = {}
    # The bank's unique key is (source_paper_id, section_title, question_number).
    # A malformed paper (LLM emitting a duplicate number, or a blank number whose
    # positional fallback collides) would otherwise raise IntegrityError and fail the
    # whole approval with a confusing 409. Disambiguate within each section instead.
    seen_numbers: set[tuple[str, str]] = set()

    for section in sections:
        section_title = section["title"] or "Section"
        for q_idx, question in enumerate(section.get("questions") or []):
            text = str(question.get("text") or "").strip()
            if not text:
                continue
            q_type = str(question.get("type") or "short")
            marks = float(question.get("marks") or 0)
            number = _question_number(question, q_idx + 1)
            if (section_title, number) in seen_numbers:
                suffix = 1
                while (section_title, f"{number}.{suffix}") in seen_numbers:
                    suffix += 1
                number = f"{number}.{suffix}"
            seen_numbers.add((section_title, number))

            question_chapter = str(question.get("chapter") or "").strip()
            # A bank item used by the exact Question Paper Studio blueprint must carry
            # question-specific scope. Older papers only have broad paper topics, so they
            # remain usable by the legacy composer but are treated as ambiguous for exact
            # chapter slots.
            item_topics = [question_chapter] if question_chapter else paper.topics
            item = QuestionBankItem(
                school_id=paper.school_id,
                class_id=paper.class_id,
                subject_id=paper.subject_id,
                source_paper_id=paper.id,
                created_by=paper.created_by,
                approved_by=approved_by,
                approved_at=approved_at,
                section_title=section_title,
                question_number=number,
                question_text=text,
                marks=marks,
                question_type=q_type,
                options=question.get("options"),
                board=paper.board,
                grade=paper.grade,
                topics=item_topics,
                source=source,
                approval_status=BANK_STATUS_APPROVED,
                content_fingerprint=content_fingerprint(
                    question_text=text, marks=marks, question_type=q_type
                ),
                usage_count=1,
                used_in_paper_ids=[paper_id_str],
                ai_model=paper.ai_model,
            )
            items.append(item)
            questions_by_key[(section_title, number)] = question
            answer_key = question.get("answer_key")
            if answer_key is not None and str(answer_key).strip():
                pending_rubrics.append((item, str(answer_key)))

    if not items:
        raise BankIngestError("Paper has no valid questions to add to the question bank")

    db.add_all(items)
    await db.flush()

    if pending_rubrics:
        db.add_all(
            RubricBankItem(question_bank_item_id=item.id, answer_key=answer_key)
            for item, answer_key in pending_rubrics
        )

    await linker.link_items_from_paper(
        paper, items, questions_by_key=questions_by_key
    )

    logger.info(
        "bank_ingest_complete",
        paper_id=str(paper.id),
        item_count=len(items),
    )
    return items


async def count_bank_items_for_paper(db: AsyncSession, paper_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(QuestionBankItem)
        .where(QuestionBankItem.source_paper_id == paper_id)
    )
    return int(result.scalar_one())


async def fetch_rubrics_for_paper(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    paper_id: uuid.UUID,
) -> dict[str, dict]:
    """Map question_number -> rubric fields for grading and misconception extraction."""
    rows = await db.execute(
        select(QuestionBankItem, RubricBankItem)
        .outerjoin(
            RubricBankItem,
            RubricBankItem.question_bank_item_id == QuestionBankItem.id,
        )
        .where(
            QuestionBankItem.school_id == school_id,
            QuestionBankItem.source_paper_id == paper_id,
            QuestionBankItem.approval_status == BANK_STATUS_APPROVED,
        )
    )
    out: dict[str, dict] = {}
    for item, rubric in rows.all():
        out[item.question_number] = {
            "question_type": item.question_type,
            "marks": float(item.marks),
            "answer_key": rubric.answer_key if rubric else None,
            "options": item.options,
            "question_text": item.question_text,
            "common_wrong_answers": rubric.common_wrong_answers if rubric else None,
            "teacher_correction_note": rubric.teacher_correction_note if rubric else None,
            "acceptable_answers": rubric.acceptable_answers if rubric else None,
        }
    return out


async def count_compose_candidates(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(QuestionBankItem)
        .where(
            QuestionBankItem.school_id == school_id,
            QuestionBankItem.class_id == class_id,
            QuestionBankItem.subject_id == subject_id,
            QuestionBankItem.approval_status == BANK_STATUS_APPROVED,
        )
    )
    return int(result.scalar_one())


async def fetch_compose_candidates(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    topics: list[str] | None = None,
) -> list[tuple[QuestionBankItem, str | None]]:
    """Approved bank items for this class+subject, with optional answer keys."""
    rows = await db.execute(
        select(QuestionBankItem, RubricBankItem.answer_key)
        .outerjoin(
            RubricBankItem,
            RubricBankItem.question_bank_item_id == QuestionBankItem.id,
        )
        .where(
            QuestionBankItem.school_id == school_id,
            QuestionBankItem.class_id == class_id,
            QuestionBankItem.subject_id == subject_id,
            QuestionBankItem.approval_status == BANK_STATUS_APPROVED,
        )
        .order_by(QuestionBankItem.created_at.desc())
    )
    candidates = [(item, answer_key) for item, answer_key in rows.all()]
    if topics:
        topic_set = {t.strip().lower() for t in topics if t.strip()}
        if topic_set:
            candidates.sort(
                key=lambda pair: -_topic_overlap_score(pair[0].topics, topic_set),
            )
    return candidates


def _topic_overlap_score(item_topics: list | None, topic_set: set[str]) -> int:
    if not item_topics:
        return 0
    return len({str(t).lower() for t in item_topics} & topic_set)


def _marks_match(bank_marks: float, slot_marks: float) -> bool:
    return abs(float(bank_marks) - float(slot_marks)) < 0.01


def _type_matches(bank_type: str, slot_type: str) -> bool:
    bt, st = bank_type.lower(), slot_type.lower()
    if bt == st:
        return True
    if st in ("very_short", "short") and bt in ("very_short", "short"):
        return True
    return False


def _matches_exact_chapter(item: QuestionBankItem, chapter: str) -> bool:
    """Return true only for an unambiguous, question-specific chapter match."""
    item_topics = [
        str(topic).strip().casefold()
        for topic in (item.topics or [])
        if str(topic).strip()
    ]
    return len(item_topics) == 1 and item_topics[0] == chapter.strip().casefold()


def bank_item_to_question(
    item: QuestionBankItem,
    answer_key: str | None,
    *,
    number: str,
) -> dict:
    question = {
        "number": number,
        "text": item.question_text,
        "marks": float(item.marks),
        "type": item.question_type,
    }
    if item.options:
        question["options"] = list(item.options)
    if answer_key:
        question["answer_key"] = answer_key
    return question


def compose_sections_from_plan(
    plan: list[dict],
    candidates: list[tuple[QuestionBankItem, str | None]],
    *,
    normalize_to_plan: bool = False,
) -> tuple[list[dict], list[uuid.UUID], list[dict]]:
    """Match bank items to blueprint slots. Returns sections, used item ids, gap specs."""
    used_ids: set[uuid.UUID] = set()
    sections: list[dict] = []
    gaps: list[dict] = []
    question_number = 1

    for spec in plan:
        title = spec["title"]
        instructions = spec.get("instructions")
        marks = float(spec["marks_per_q"])
        qtype = spec["type"]
        need = int(spec.get("answer_any", spec["count"]))
        questions: list[dict] = []
        missing = 0

        for _ in range(need):
            matched: tuple[QuestionBankItem, str | None] | None = None
            for item, answer_key in candidates:
                if item.id in used_ids:
                    continue
                if not _marks_match(item.marks, marks):
                    continue
                if not _type_matches(item.question_type, qtype):
                    continue
                matched = (item, answer_key)
                break
            if matched:
                item, answer_key = matched
                used_ids.add(item.id)
                question = bank_item_to_question(
                    item, answer_key, number=str(question_number)
                )
                if normalize_to_plan:
                    # The exact slot contract is authoritative. `_marks_match` and
                    # `_type_matches` already proved semantic compatibility; normalize the
                    # representation (e.g. short -> very_short) only for custom plans.
                    question["marks"] = marks
                    question["type"] = qtype
                questions.append(question)
                question_number += 1
            else:
                missing += 1

        if missing:
            gaps.append({
                "section_title": title,
                "instructions": instructions,
                "marks": marks,
                "type": qtype,
                "count": missing,
            })
        sections.append({
            "title": title,
            "instructions": instructions,
            "questions": questions,
        })

    return sections, list(used_ids), gaps


def compose_exact_sections_from_plan(
    plan: list[dict],
    candidates: list[tuple[QuestionBankItem, str | None]],
    blueprint_slots: dict[tuple[int, int], dict],
) -> tuple[list[dict], list[uuid.UUID], list[dict]]:
    """Compose exact blueprint slots without relabelling unrelated bank questions.

    Existing bank rows whose topic metadata is missing or broad are intentionally treated as
    gaps. A teacher-authored chapter/Bloom slot is evidence, not a label that may be overlaid on
    an arbitrary marks/type match.
    """
    used_ids: set[uuid.UUID] = set()
    sections: list[dict] = []
    gaps: list[dict] = []
    question_number = 1

    for section_index, spec in enumerate(plan):
        title = spec["title"]
        instructions = spec.get("instructions")
        marks = float(spec["marks_per_q"])
        qtype = str(spec["type"])
        questions: list[dict] = []

        for question_index in range(int(spec["count"])):
            slot = blueprint_slots[(section_index, question_index)]
            matched: tuple[QuestionBankItem, str | None] | None = None
            for item, answer_key in candidates:
                if item.id in used_ids:
                    continue
                if not answer_key or not str(answer_key).strip():
                    continue
                if not _marks_match(item.marks, marks):
                    continue
                if not _type_matches(item.question_type, qtype):
                    continue
                if not _matches_exact_chapter(item, slot["chapter"]):
                    continue
                if qtype == "mcq" and (
                    not isinstance(item.options, list)
                    or len(item.options) != 4
                    or any(not str(option).strip() for option in item.options)
                ):
                    continue
                matched = (item, answer_key)
                break

            if matched:
                item, answer_key = matched
                used_ids.add(item.id)
                question = bank_item_to_question(
                    item, answer_key, number=str(question_number)
                )
                question["marks"] = marks
                question["type"] = qtype
                question["_blueprint_slot"] = [section_index, question_index]
                questions.append(question)
                question_number += 1
            else:
                gaps.append({
                    "section_title": title,
                    "section_index": section_index,
                    "question_index": question_index,
                    "instructions": instructions,
                    "marks": marks,
                    "type": qtype,
                    "chapter": slot["chapter"],
                    "bloom": slot["bloom"],
                })

        sections.append({
            "title": title,
            "instructions": instructions,
            "questions": questions,
        })

    return sections, list(used_ids), gaps


def merge_exact_gap_fill(
    sections: list[dict],
    fills: list[dict],
    *,
    plan: list[dict],
    gaps: list[dict],
) -> list[dict]:
    """Merge coordinate-addressed fills and restore exact teacher blueprint order."""
    expected_gap_coordinates = {
        (int(gap["section_index"]), int(gap["question_index"])) for gap in gaps
    }
    by_coordinate: dict[tuple[int, int], dict] = {}

    for section in sections:
        for raw_question in section.get("questions") or []:
            marker = raw_question.get("_blueprint_slot")
            if not isinstance(marker, list) or len(marker) != 2:
                raise ValueError("Bank question is missing its exact blueprint coordinate")
            coordinate = (int(marker[0]), int(marker[1]))
            question = dict(raw_question)
            question.pop("_blueprint_slot", None)
            by_coordinate[coordinate] = question

    seen_fill_coordinates: set[tuple[int, int]] = set()
    for fill in fills:
        if not isinstance(fill, dict):
            raise ValueError("Each exact gap fill must be an object")
        try:
            coordinate = (int(fill["section_index"]), int(fill["question_index"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Exact gap fills require integer section/question coordinates"
            ) from exc
        if coordinate not in expected_gap_coordinates:
            raise ValueError("AI returned an unexpected exact gap coordinate")
        if coordinate in seen_fill_coordinates:
            raise ValueError("AI returned a duplicate exact gap coordinate")
        seen_fill_coordinates.add(coordinate)
        question = {
            "number": "",
            "text": str(fill.get("text") or ""),
            "marks": float(fill.get("marks", 0) or 0),
            "type": str(fill.get("type") or "short"),
        }
        if fill.get("options") is not None:
            question["options"] = list(fill.get("options") or [])
        if fill.get("answer_key") is not None:
            question["answer_key"] = str(fill.get("answer_key"))
        by_coordinate[coordinate] = question

    merged: list[dict] = []
    for section_index, spec in enumerate(plan):
        ordered_questions = [
            by_coordinate[(section_index, question_index)]
            for question_index in range(int(spec["count"]))
            if (section_index, question_index) in by_coordinate
        ]
        merged.append({
            "title": spec["title"],
            "instructions": spec.get("instructions"),
            "questions": ordered_questions,
        })
    return merged


def merge_gap_fill(sections: list[dict], fills: list[dict]) -> list[dict]:
    """Append LLM-generated gap questions into composed sections by title."""
    by_title: dict[str, list] = {}
    for fill in fills:
        title = str(fill.get("section_title") or "")
        by_title.setdefault(title, []).extend(fill.get("questions") or [])

    merged: list[dict] = []
    for section in sections:
        title = section["title"]
        questions = list(section.get("questions") or [])
        for raw in by_title.get(title, []):
            q = {
                "number": str(raw.get("number", "")),
                "text": str(raw.get("text", "")),
                "marks": float(raw.get("marks", 0) or 0),
                "type": str(raw.get("type", "short")),
            }
            if raw.get("options"):
                q["options"] = [str(o) for o in raw["options"]]
            if raw.get("answer_key") is not None:
                q["answer_key"] = str(raw.get("answer_key"))
            if q["text"].strip():
                questions.append(q)
        merged.append({**section, "questions": questions})
    return merged


def renumber_sections(sections: list[dict]) -> list[dict]:
    """Sequential question numbers across the whole paper."""
    n = 1
    out: list[dict] = []
    for section in sections:
        questions = []
        for q in section.get("questions") or []:
            questions.append({**q, "number": str(n)})
            n += 1
        out.append({**section, "questions": questions})
    return out


async def note_bank_items_used(
    db: AsyncSession,
    item_ids: list[uuid.UUID],
    paper_id: uuid.UUID,
) -> None:
    if not item_ids:
        return
    paper_id_str = str(paper_id)
    rows = await db.execute(
        select(QuestionBankItem).where(QuestionBankItem.id.in_(item_ids))
    )
    for item in rows.scalars().all():
        item.usage_count = int(item.usage_count or 0) + 1
        used = list(item.used_in_paper_ids or [])
        if paper_id_str not in used:
            used.append(paper_id_str)
            item.used_in_paper_ids = used
