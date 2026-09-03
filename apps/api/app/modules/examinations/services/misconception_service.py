"""Misconception library — extract teaching memory from approved evaluations."""
from __future__ import annotations

import hashlib
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.answer_sheet_evaluation import AnswerSheetEvaluation
from app.db.models.examination import Exam
from app.db.models.misconception import MisconceptionEntry
from app.modules.ai.services.question_bank_service import fetch_rubrics_for_paper

_WHITESPACE = re.compile(r"\s+")


def _fingerprint(*, topic: str, mistake: str) -> str:
    norm = _WHITESPACE.sub(" ", mistake.strip().lower())
    payload = f"{topic.strip().lower()}|{norm}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _topic_for_question(exam: Exam, qno: str) -> str:
    for q in exam.question_schema or []:
        if str(q.get("no")) == qno:
            t = q.get("topic")
            if t and str(t).strip():
                return str(t).strip()
    return (exam.topic or "General").strip() or "General"


def _build_mistake_text(
    *,
    student_answer: str,
    feedback: str,
    answer_key: str,
    common_wrong: list | None,
) -> str:
    if student_answer.strip():
        return f"Wrote: {student_answer.strip()[:300]}"
    if feedback.strip():
        return feedback.strip()[:400]
    if common_wrong:
        return f"Common pattern: {common_wrong[0]}"
    if answer_key:
        return f"Did not match expected: {answer_key[:200]}"
    return "Incorrect response"


def _remedial_hint(
    *,
    topic: str,
    rubric_note: str | None,
    common_wrong: list | None,
) -> str:
    if rubric_note and rubric_note.strip():
        return rubric_note.strip()[:500]
    if common_wrong and len(common_wrong) > 1:
        return (
            f"Review why '{common_wrong[0]}' is wrong; "
            f"contrast with correct approach for {topic}."
        )
    return f"Short revision activity on {topic} — worked examples + 3 practice questions."


async def extract_from_evaluation(
    db: AsyncSession,
    *,
    evaluation: AnswerSheetEvaluation,
    exam: Exam,
    approved_by: uuid.UUID,
) -> list[MisconceptionEntry]:
    """Upsert misconception rows for partially wrong questions."""
    if not evaluation.ai_suggestions or not exam.source_paper_id:
        return []

    rubrics = await fetch_rubrics_for_paper(
        db, school_id=evaluation.school_id, paper_id=exam.source_paper_id
    )
    created: list[MisconceptionEntry] = []

    for qno, suggestion in evaluation.ai_suggestions.items():
        max_m = float(suggestion.get("max_marks", 0))
        suggested = float(suggestion.get("marks_suggested", 0))
        if suggested >= max_m:
            continue

        topic = _topic_for_question(exam, qno)
        rubric = rubrics.get(qno, {})
        mistake = _build_mistake_text(
            student_answer=str(suggestion.get("student_answer") or ""),
            feedback=str(suggestion.get("feedback") or ""),
            answer_key=str(rubric.get("answer_key") or ""),
            common_wrong=rubric.get("common_wrong_answers"),
        )
        fp = _fingerprint(topic=topic, mistake=mistake)
        remedial = _remedial_hint(
            topic=topic,
            rubric_note=rubric.get("teacher_correction_note"),
            common_wrong=rubric.get("common_wrong_answers"),
        )

        existing = (
            await db.execute(
                select(MisconceptionEntry).where(
                    MisconceptionEntry.school_id == evaluation.school_id,
                    MisconceptionEntry.content_fingerprint == fp,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.occurrence_count = int(existing.occurrence_count or 0) + 1
            existing.source_evaluation_id = evaluation.id
            created.append(existing)
            continue

        row = MisconceptionEntry(
            school_id=evaluation.school_id,
            class_id=exam.class_id,
            subject_id=exam.subject_id,
            topic=topic,
            question_no=qno,
            common_mistake=mistake,
            remedial_activity=remedial,
            source_evaluation_id=evaluation.id,
            student_id=evaluation.student_id,
            created_by=approved_by,
            content_fingerprint=fp,
        )
        db.add(row)
        created.append(row)

    await db.flush()
    return created


async def list_misconceptions(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    class_id: uuid.UUID | None = None,
    topic: str | None = None,
    subject_ids: set[uuid.UUID] | None = None,
    limit: int = 50,
) -> list[MisconceptionEntry]:
    query = select(MisconceptionEntry).where(MisconceptionEntry.school_id == school_id)
    if class_id:
        query = query.where(MisconceptionEntry.class_id == class_id)
    if subject_ids is not None:
        if not subject_ids:
            return []
        query = query.where(MisconceptionEntry.subject_id.in_(subject_ids))
    if topic:
        query = query.where(MisconceptionEntry.topic.ilike(f"%{topic.strip()}%"))
    result = await db.execute(
        query.order_by(MisconceptionEntry.occurrence_count.desc()).limit(limit)
    )
    return list(result.scalars().all())
