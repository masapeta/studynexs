"""Deterministic learning-evidence composition for mastery review and workspace reads."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.answer_sheet_evaluation import EVAL_STATUS_APPROVED, AnswerSheetEvaluation
from app.db.models.examination import Exam, ExamMark
from app.db.models.mastery import MasteryFlag, StudentTopicMastery
from app.db.models.misconception import MisconceptionEntry
from app.db.models.question_paper import QuestionPaper
from app.modules.mastery.schemas.mastery import (
    LearningEvidenceChainOut,
    LearningEvidenceExamOut,
    TopicMasteryOut,
)


def _history_exam_ids(history: list[dict]) -> list[uuid.UUID]:
    exam_ids: list[uuid.UUID] = []
    for item in history:
        raw = item.get("exam_id") if isinstance(item, dict) else None
        if not raw:
            continue
        try:
            exam_ids.append(uuid.UUID(str(raw)))
        except (TypeError, ValueError):
            continue
    return exam_ids


def _citation_count(paper: QuestionPaper | None) -> int:
    if not paper or not paper.grounding_sources:
        return 0
    return len(paper.grounding_sources)


async def build_learning_evidence_chain(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    tenant_slug: str,
    flag: MasteryFlag,
) -> LearningEvidenceChainOut:
    ledger = (
        await db.execute(
            select(StudentTopicMastery).where(
                StudentTopicMastery.school_id == school_id,
                StudentTopicMastery.student_id == flag.student_id,
                StudentTopicMastery.class_id == flag.class_id,
                StudentTopicMastery.subject_id == flag.subject_id,
                StudentTopicMastery.academic_year_id == flag.academic_year_id,
                StudentTopicMastery.topic == flag.topic,
            )
        )
    ).scalar_one_or_none()

    history = list(
        (ledger.history if ledger else None) or (flag.evidence or {}).get("history") or []
    )
    exam_ids = _history_exam_ids(history)
    topic_pct_by_exam = {
        str(item.get("exam_id")): item.get("pct")
        for item in history
        if isinstance(item, dict) and item.get("exam_id")
    }

    exams = []
    if exam_ids:
        exams = list(
            (
                await db.execute(
                    select(Exam).where(Exam.school_id == school_id, Exam.id.in_(exam_ids))
                )
            )
            .scalars()
            .all()
        )
    exams_by_id = {exam.id: exam for exam in exams}

    marks = []
    if exam_ids:
        marks = list(
            (
                await db.execute(
                    select(ExamMark).where(
                        ExamMark.school_id == school_id,
                        ExamMark.student_id == flag.student_id,
                        ExamMark.exam_id.in_(exam_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
    marks_by_exam = {mark.exam_id: mark for mark in marks}

    paper_ids = [exam.source_paper_id for exam in exams if exam.source_paper_id]
    papers = []
    if paper_ids:
        papers = list(
            (
                await db.execute(
                    select(QuestionPaper).where(
                        QuestionPaper.school_id == school_id,
                        QuestionPaper.id.in_(paper_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
    papers_by_id = {paper.id: paper for paper in papers}

    evaluations = []
    if exam_ids:
        evaluations = list(
            (
                await db.execute(
                    select(AnswerSheetEvaluation).where(
                        AnswerSheetEvaluation.school_id == school_id,
                        AnswerSheetEvaluation.student_id == flag.student_id,
                        AnswerSheetEvaluation.exam_id.in_(exam_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
    evals_by_exam: dict[uuid.UUID, list[AnswerSheetEvaluation]] = {}
    for evaluation in evaluations:
        evals_by_exam.setdefault(evaluation.exam_id, []).append(evaluation)

    misconception_rows = list(
        (
            await db.execute(
                select(MisconceptionEntry).where(
                    MisconceptionEntry.school_id == school_id,
                    MisconceptionEntry.student_id == flag.student_id,
                    MisconceptionEntry.class_id == flag.class_id,
                    MisconceptionEntry.subject_id == flag.subject_id,
                    MisconceptionEntry.topic.ilike(f"%{flag.topic_display}%"),
                )
            )
        )
        .scalars()
        .all()
    )

    from app.modules.knowledge_graph.services.student_weak_concept_service import (
        StudentWeakConceptService,
    )

    weak_concepts = await StudentWeakConceptService(db).get_weak_concepts_for_student(
        school_id=school_id,
        student_id=flag.student_id,
        subject_id=flag.subject_id,
    )
    matching_weak_concepts = [
        (concept, meta)
        for concept, meta in weak_concepts
        if (meta or {}).get("topic", "").strip().casefold()
        == flag.topic_display.strip().casefold()
    ]

    chain_exams: list[LearningEvidenceExamOut] = []
    for exam_id in exam_ids:
        exam = exams_by_id.get(exam_id)
        if not exam:
            continue
        mark = marks_by_exam.get(exam.id)
        paper = papers_by_id.get(exam.source_paper_id) if exam.source_paper_id else None
        exam_evals = evals_by_exam.get(exam.id, [])
        approved_evals = [e for e in exam_evals if e.status == EVAL_STATUS_APPROVED]
        raw_pct = topic_pct_by_exam.get(str(exam.id))
        try:
            topic_pct = float(raw_pct) if raw_pct is not None else None
        except (TypeError, ValueError):
            topic_pct = None
        chain_exams.append(
            LearningEvidenceExamOut(
                exam_id=exam.id,
                title=exam.title,
                exam_type=exam.exam_type.value,
                assessed_on=exam.date,
                marks_obtained=float(mark.marks_obtained) if mark else None,
                total_marks=float(exam.total_marks) if exam.total_marks is not None else None,
                topic_pct=topic_pct,
                question_paper_id=exam.source_paper_id,
                curriculum_pack_id=paper.pack_id if paper else None,
                question_paper_grounded=bool(paper and paper.grounded),
                citation_count=_citation_count(paper),
                evaluation_ids=[e.id for e in exam_evals],
                approved_evaluation_ids=[e.id for e in approved_evals],
            )
        )

    curriculum_pack_ids = sorted(
        {row.curriculum_pack_id for row in chain_exams if row.curriculum_pack_id},
        key=str,
    )
    question_paper_ids = sorted(
        {row.question_paper_id for row in chain_exams if row.question_paper_id},
        key=str,
    )
    evaluation_ids = sorted({eid for row in chain_exams for eid in row.evaluation_ids}, key=str)
    approved_evaluation_ids = sorted(
        {eid for row in chain_exams for eid in row.approved_evaluation_ids},
        key=str,
    )
    weak_concept_pack_ids = sorted(
        {concept.pack_id for concept, _meta in matching_weak_concepts},
        key=str,
    )

    warnings: list[str] = []
    if ledger is None:
        warnings.append("mastery_ledger_missing")
    if not chain_exams:
        warnings.append("assessment_history_missing")
    if not question_paper_ids:
        warnings.append("question_paper_link_missing")
    if not curriculum_pack_ids:
        warnings.append("curriculum_pack_link_missing")
    if not any(row.question_paper_grounded for row in chain_exams):
        warnings.append("grounded_question_paper_missing")
    if ledger and float(ledger.mastery_pct) < 70 and not matching_weak_concepts:
        warnings.append("weak_concept_kg_link_missing")

    return LearningEvidenceChainOut(
        tenant_slug=tenant_slug,
        school_id=school_id,
        flag_id=flag.id,
        student_id=flag.student_id,
        class_id=flag.class_id,
        subject_id=flag.subject_id,
        topic=flag.topic,
        topic_display=flag.topic_display,
        flag_status=flag.status,
        reviewed_by=flag.reviewed_by,
        reviewed_at=flag.reviewed_at,
        notified_at=flag.notified_at,
        mastery=TopicMasteryOut.model_validate(ledger) if ledger else None,
        exams=chain_exams,
        curriculum_pack_ids=curriculum_pack_ids,
        question_paper_ids=question_paper_ids,
        evaluation_ids=evaluation_ids,
        approved_evaluation_ids=approved_evaluation_ids,
        weak_concept_count=len(matching_weak_concepts),
        weak_concept_pack_ids=weak_concept_pack_ids,
        misconception_count=len(misconception_rows),
        parent_note_available=bool((flag.narrative or "").strip()),
        parent_notified=bool(flag.notified_at),
        grounded=bool(
            curriculum_pack_ids and any(row.question_paper_grounded for row in chain_exams)
        ),
        fallback=bool(warnings),
        warnings=warnings,
    )
