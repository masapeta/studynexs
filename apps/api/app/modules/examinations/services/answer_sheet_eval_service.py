"""Answer sheet evaluation — vision OCR, async jobs, HITL approve, misconception extract."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings
from app.core.tenant_scope import TenantScope
from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_FAILED,
    EVAL_STATUS_PROCESSING,
    EVAL_STATUS_SUGGESTED,
    AnswerSheetEvaluation,
)
from app.db.models.examination import Exam, ExamMark
from app.db.models.question_paper import QuestionPaper
from app.db.models.school import School
from app.db.models.student import Student
from app.modules.ai.gateway.base import LLMResult
from app.modules.ai.services.ai_credits import (
    assert_credits_for_charge,
    check_ai_credits,
    credits_for_purpose,
)
from app.modules.ai.services.assessment_grounding import ground_for_evaluation, resolve_citations
from app.modules.ai.services.evaluation_engine import SubjectiveItem, evaluate_subjective
from app.modules.ai.services.question_bank_service import fetch_rubrics_for_paper
from app.modules.eui.services.aei_consumer_migration import (
    observe_aei_consumer_migration,
    summarize_aei_passive_capture,
    summarize_legacy_evaluation,
)
from app.modules.eui.services.aei_consumer_migration_evidence import (
    bind_aei_consumer_migration_evidence,
)
from app.modules.examinations.schemas.evaluation import EvaluationApprove
from app.modules.examinations.schemas.exam import MarkEntry
from app.modules.examinations.services.aei_activation_trust import (
    activation_trust_profile_enabled,
    observe_activation_trust_suggestions,
    validate_and_merge_manual_review_acknowledgements,
)
from app.modules.examinations.services.aei_passive_integration import (
    observe_answer_sheet_evaluation,
)
from app.modules.examinations.services.aei_v1_language_ocr_assist import (
    ANSWER_SOURCE_OCR_IMAGE,
    ANSWER_SOURCE_TEACHER_TEXT,
    apply_language_ocr_assist_metadata,
)
from app.modules.examinations.services.aei_v1_math_normalization import (
    evaluate_math_normalization,
)
from app.modules.examinations.services.aei_v1_review_policy import (
    apply_review_policy_metadata,
    normalize_teacher_overrides_for_review_policy,
)
from app.modules.examinations.services.aei_v1_visual_science_assist import (
    apply_visual_science_assist_metadata,
)
from app.modules.examinations.services.answer_sheet_vision import (
    extract_answers_from_image,
    is_image_mime,
)
from app.modules.examinations.services.exam_service import ExamService
from app.modules.examinations.services.misconception_service import extract_from_evaluation
from app.modules.files.services.file_service import FileService
from app.modules.files.services.file_validation import read_file_bytes_bounded

logger = structlog.get_logger()
settings = get_settings()

_WHITESPACE = re.compile(r"\s+")
_OBJECTIVE_TYPES = frozenset({"mcq", "fill_blank", "true_false", "fill_in_blank"})
# A short/very-short answer with a compact key is graded deterministically (exact match);
# anything longer is treated as open-ended and routed to the marking engine.
_OBJECTIVE_ANSWER_MAXLEN = 40


class EvalError(ValueError):
    """Evaluation cannot proceed."""


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text.strip().lower())


def _mcq_letter(answer: str, options: list | None) -> str | None:
    raw = answer.strip()
    if len(raw) == 1 and raw.upper() in "ABCDEFGH":
        return raw.upper()
    if not options:
        return raw.upper() if raw else None
    norm = _normalize(raw)
    for idx, opt in enumerate(options):
        if _normalize(str(opt)) == norm:
            return chr(ord("A") + idx)
    return raw.upper() if raw else None


def grade_objective(
    *,
    q_type: str,
    student_answer: str,
    answer_key: str,
    max_marks: float,
    options: list | None = None,
) -> tuple[float, str, float]:
    if not student_answer.strip():
        return 0.0, "No answer provided.", 0.9

    q = q_type.lower()
    key = answer_key.strip()
    if q == "mcq":
        student_letter = _mcq_letter(student_answer, options)
        key_letter = _mcq_letter(key, options) or key.upper()
        if student_letter and key_letter and student_letter == key_letter:
            return max_marks, "Correct option selected.", 0.98
        return (
            0.0,
            f"Selected {student_letter or student_answer}; expected {key_letter or key}.",
            0.95,
        )

    if q in ("true_false", "fill_blank", "fill_in_blank"):
        if _normalize(student_answer) == _normalize(key):
            return max_marks, "Correct answer.", 0.98
        return 0.0, f"Expected '{key}'.", 0.95

    if _normalize(student_answer) == _normalize(key):
        return max_marks, "Matches model answer.", 0.95
    return 0.0, "Does not match model answer.", 0.85


def grade_subjective_heuristic(
    *,
    student_answer: str,
    answer_key: str,
    max_marks: float,
) -> tuple[float, str, float]:
    if not student_answer.strip():
        return 0.0, "No answer provided.", 0.9
    if not answer_key.strip():
        return 0.0, "No model answer on file — teacher must mark manually.", 0.3

    key_tokens = {t for t in re.findall(r"[a-z0-9]+", _normalize(answer_key)) if len(t) > 2}
    ans_tokens = {t for t in re.findall(r"[a-z0-9]+", _normalize(student_answer)) if len(t) > 2}
    if not key_tokens:
        return 0.0, "Review manually.", 0.4

    overlap = len(key_tokens & ans_tokens) / len(key_tokens)
    if overlap >= 0.7:
        return max_marks, "Strong match to model answer.", 0.75
    if overlap >= 0.4:
        return round(max_marks * 0.5, 2), "Partial match — review suggested.", 0.55
    return 0.0, "Weak match to model answer.", 0.6


def _build_summary(suggestions: dict[str, dict]) -> str:
    ordered = sorted(
        suggestions.items(),
        key=lambda x: int(x[0]) if x[0].isdigit() else x[0],
    )
    weak = [
        f"Q{qno}: {s.get('feedback', '')}"
        for qno, s in ordered
        if float(s.get("marks_suggested", 0)) < float(s.get("max_marks", 0))
    ]
    if not weak:
        return "All questions appear fully correct per rubric."
    return "Areas to review:\n" + "\n".join(weak[:8])


class AnswerSheetEvalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_and_evaluate(
        self,
        *,
        school_id: uuid.UUID,
        exam_id: uuid.UUID,
        student_id: uuid.UUID,
        created_by: uuid.UUID,
        role: str,
        school: School,
        file_id: uuid.UUID | None = None,
        student_answers: dict[str, str] | None = None,
    ) -> AnswerSheetEvaluation:
        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(exam_id)
        if not exam.source_paper_id:
            raise EvalError("Exam is not linked to an approved AI question paper")
        if not exam.question_schema:
            raise EvalError("Exam has no question schema")
        if not file_id and not (student_answers or {}):
            raise EvalError("Upload an answer sheet image or provide student answers")

        await scope.students_in_class(exam.class_id, [student_id])
        await check_ai_credits(
            self.db, school, user_id=created_by, role=role, purpose_tag="exam_evaluation"
        )
        await self.db.execute(
            select(Student.id)
            .where(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.class_id == exam.class_id,
            )
            .with_for_update()
        )

        existing = (
            await self.db.execute(
                select(AnswerSheetEvaluation)
                .where(
                    AnswerSheetEvaluation.exam_id == exam_id,
                    AnswerSheetEvaluation.student_id == student_id,
                    AnswerSheetEvaluation.school_id == school_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if existing and existing.status == EVAL_STATUS_APPROVED:
            raise EvalError("Marks already approved for this student — edit marks directly")
        if existing and existing.status == EVAL_STATUS_PROCESSING:
            raise EvalError("Evaluation already in progress for this student")

        if existing:
            row = existing
            row.file_id = file_id
            row.input_answers = dict(student_answers or {})
            row.status = EVAL_STATUS_PROCESSING
            row.ai_suggestions = None
            row.correction_summary = None
            row.teacher_overrides = None
            row.error_message = None
            row.job_id = None
            row.created_by = created_by
        else:
            row = AnswerSheetEvaluation(
                school_id=school_id,
                exam_id=exam_id,
                student_id=student_id,
                file_id=file_id,
                input_answers=dict(student_answers or {}),
                created_by=created_by,
                status=EVAL_STATUS_PROCESSING,
            )
            self.db.add(row)
        await self.db.flush()

        if settings.ENVIRONMENT == Environment.TESTING:
            return await self.execute_evaluation(row.id, role=role)

        try:
            from app.core.jobs.queue import enqueue

            job = await enqueue(
                self.db,
                task="answer_sheet_eval",
                params={"evaluation_id": str(row.id), "role": role},
                school_id=school_id,
                created_by=created_by,
            )
            row.job_id = job.id
            await self.db.flush()
            return row
        except Exception:
            logger.warning("eval_enqueue_failed_running_sync", evaluation_id=str(row.id))
            return await self.execute_evaluation(row.id, role=role)

    async def execute_evaluation(
        self, evaluation_id: uuid.UUID, *, role: str = "teacher"
    ) -> AnswerSheetEvaluation:
        result = await self.db.execute(
            select(AnswerSheetEvaluation).where(AnswerSheetEvaluation.id == evaluation_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise EvalError("Evaluation not found")

        scope = TenantScope(self.db, row.school_id)
        exam = await scope.exam(row.exam_id)
        row.status = EVAL_STATUS_PROCESSING
        await self.db.flush()

        vision_result = None
        try:
            answers, vision_result, answer_sources = await self._resolve_student_answers(
                row, exam
            )
            suggestions, subjective_results = await self._grade_exam(
                exam=exam,
                school_id=row.school_id,
                student_answers=answers,
                answer_sources=answer_sources,
            )
            observe_activation_trust_suggestions(
                enabled=activation_trust_profile_enabled(settings),
                suggestions=suggestions,
            )
            passive_capture = await observe_answer_sheet_evaluation(
                enabled=(
                    settings.AEI_PASSIVE_INTEGRATION_ENABLED
                    or settings.AEI_SHADOW_MODE_ENABLED
                    or settings.EUI_CONSUMER_AEI_DUAL_READ_ENABLED
                ),
                shadow_enabled=settings.AEI_SHADOW_MODE_ENABLED,
                db=self.db,
                evaluation_id=row.id,
                school_id=row.school_id,
                exam=exam,
                student_id=row.student_id,
                student_answers=answers,
                suggestions=suggestions,
            )
            rich_evidence = await bind_aei_consumer_migration_evidence(
                enabled=(
                    settings.EUI_CONSUMER_AEI_DUAL_READ_ENABLED
                    and settings.EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED
                ),
                db=self.db,
                tenant_id=row.school_id,
                subject_type="answer_sheet_evaluation",
                subject_ref=f"answer_sheet_evaluation:{row.id}",
                artifact_id=row.id,
                exam=exam,
            )
            eui_summary = summarize_aei_passive_capture(passive_capture)
            if rich_evidence is not None:
                eui_summary.update(rich_evidence.eui_summary)
            observe_aei_consumer_migration(
                enabled=settings.EUI_CONSUMER_AEI_DUAL_READ_ENABLED,
                tenant_id=row.school_id,
                subject_type="answer_sheet_evaluation",
                subject_ref=f"answer_sheet_evaluation:{row.id}",
                legacy_summary=summarize_legacy_evaluation(suggestions),
                eui_summary=eui_summary,
                educational_context=(
                    rich_evidence.educational_context
                    if rich_evidence is not None
                    else None
                ),
                capability_lookup=(
                    rich_evidence.capability_lookup if rich_evidence is not None else None
                ),
                trust_report=rich_evidence.trust_report if rich_evidence is not None else None,
                source_enabled=settings.EUI_CONSUMER_AEI_SOURCE_ENABLED,
            )
            row.ai_suggestions = suggestions
            row.correction_summary = _build_summary(suggestions)
            row.status = EVAL_STATUS_SUGGESTED
            # One evaluation = one credit charge. Vision (if any) leads, then subjective marking
            # calls are recorded cost-only for observability. _record_eval_credits keeps the
            # single-charge invariant and is idempotent across re-runs.
            llm_results: list[LLMResult] = []
            if isinstance(vision_result, LLMResult):
                llm_results.append(vision_result)
            llm_results.extend(subjective_results)
            await self._record_eval_credits(
                school_id=row.school_id,
                created_by=row.created_by,
                role=role,
                evaluation_id=row.id,
                llm_results=llm_results,
            )
        except Exception as exc:
            logger.exception("eval_failed", evaluation_id=str(evaluation_id))
            row.status = EVAL_STATUS_FAILED
            row.error_message = "Evaluation failed. Try again or enter marks manually."
            await self.db.flush()
            raise EvalError(row.error_message) from exc

        await self.db.flush()
        return row

    async def _resolve_student_answers(
        self,
        row: AnswerSheetEvaluation,
        exam: Exam,
    ) -> tuple[dict[str, str], object | None, dict[str, str]]:
        merged = dict(row.input_answers or {})
        answer_sources = {
            str(qno): ANSWER_SOURCE_TEACHER_TEXT
            for qno, value in merged.items()
            if str(value).strip()
        }
        vision_result = None

        if row.file_id:
            file_svc = FileService(self.db)
            record = await file_svc.get_file(row.file_id, row.school_id)
            if not record:
                raise EvalError("Answer sheet file not found")
            if is_image_mime(record.content_type):
                try:
                    image_bytes = read_file_bytes_bounded(
                        record.storage_path,
                        size_bytes=record.size_bytes,
                    )
                except ValueError as exc:
                    raise EvalError(
                        "Answer sheet file is too large or unreadable"
                    ) from exc
                rubrics = await fetch_rubrics_for_paper(
                    self.db, school_id=row.school_id, paper_id=exam.source_paper_id
                )
                extracted, vision_result = await extract_answers_from_image(
                    image_bytes=image_bytes,
                    mime_type=record.content_type,
                    question_schema=exam.question_schema or [],
                    rubrics=rubrics,
                )
                for qno, text in extracted.items():
                    if qno not in merged or not str(merged.get(qno, "")).strip():
                        merged[qno] = text
                        answer_sources[str(qno)] = ANSWER_SOURCE_OCR_IMAGE

        return merged, vision_result, answer_sources

    async def _record_eval_credits(
        self,
        *,
        school_id: uuid.UUID,
        created_by: uuid.UUID,
        role: str,
        evaluation_id: uuid.UUID,
        llm_results: list[LLMResult] | None = None,
    ) -> None:
        """Charge exactly one credit per evaluation; log every real LLM call for observability.

        An evaluation may fan out to several provider calls (vision OCR + one subjective marking
        call). The school is billed once: the first LLM call carries the credit, the rest are
        recorded cost-only. When no LLM ran (pure heuristic), an ``internal`` row carries the
        charge. Idempotent — a re-run finds the existing charged row and does nothing.
        """
        from app.db.models.ai_usage import AIUsage
        from app.modules.ai.gateway.metering import record_usage

        existing = (
            await self.db.execute(
                select(AIUsage.id).where(
                    AIUsage.school_id == school_id,
                    AIUsage.ref_type == "answer_sheet_evaluation",
                    AIUsage.ref_id == evaluation_id,
                    AIUsage.credits_charged > 0,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if existing:
            return

        credits = credits_for_purpose("exam_evaluation")
        results = [r for r in (llm_results or []) if isinstance(r, LLMResult)]

        if results:
            # First call carries the credit (record_usage enforces caps at INSERT); the rest are
            # cost-only observability rows so a school is never billed per question.
            for idx, result in enumerate(results):
                await record_usage(
                    self.db,
                    feature="answer_sheet_eval",
                    result=result,
                    school_id=school_id,
                    created_by=created_by,
                    role=role,
                    purpose_tag="exam_evaluation",
                    credits_charged=credits if idx == 0 else 0,
                    ref_type="answer_sheet_evaluation",
                    ref_id=evaluation_id,
                    image_count=1 if idx == 0 else 0,
                )
            return

        await assert_credits_for_charge(
            self.db,
            school_id,
            user_id=created_by,
            role=role,
            purpose_tag="exam_evaluation",
            credits=credits,
        )
        self.db.add(
            AIUsage(
                school_id=school_id,
                created_by=created_by,
                feature="answer_sheet_eval",
                provider="internal",
                model="heuristic-v1",
                tokens_in=0,
                tokens_out=0,
                cost_usd=0,
                latency_ms=0,
                role=role,
                purpose_tag="exam_evaluation",
                credits_charged=credits,
                ref_type="answer_sheet_evaluation",
                ref_id=evaluation_id,
            )
        )

    @staticmethod
    def _is_objective(q_type: str, answer_key: str) -> bool:
        """Objective = deterministic key-match (MCQ/T-F/fill), or a very-short factual key.

        Objective grading is exact and never touches the LLM (DECISION_LOG §3.6); only genuinely
        open-ended answers go to the marking engine.
        """
        t = q_type.lower()
        if t in _OBJECTIVE_TYPES:
            return True
        return (
            t in ("short", "very_short")
            and bool(answer_key)
            and len(answer_key) < _OBJECTIVE_ANSWER_MAXLEN
        )

    @staticmethod
    def _make_suggestion(
        *,
        marks: float,
        max_marks: float,
        feedback: str,
        confidence: float,
        student_answer: str,
        topic: str | None,
        method: str,
        misconception_hint: str | None = None,
        criteria: list | None = None,
        missing_concepts: list | None = None,
        citations: list[int] | None = None,
        grounding_sources: list[dict] | None = None,
        grounded: bool = False,
    ) -> dict:
        """One question's suggestion, in the shape the approve flow + corrections history expect.

        ``method`` records how the mark was produced (``objective`` | ``llm_rubric`` |
        ``heuristic_fallback``) so the UI can show provenance and the teacher stays the authority.
        """
        return {
            "marks_suggested": marks,
            "max_marks": max_marks,
            "feedback": feedback,
            "confidence": confidence,
            "student_answer": student_answer,
            "topic": topic,
            "misconception_hint": misconception_hint,
            "ocr_source": bool(student_answer),
            "method": method,
            "criteria": criteria or [],
            "missing_concepts": missing_concepts or [],
            "citations": citations or [],
            "grounding_sources": grounding_sources or [],
            "grounded": grounded,
        }

    async def _grade_exam(
        self,
        *,
        exam: Exam,
        school_id: uuid.UUID,
        student_answers: dict[str, str],
        answer_sources: dict[str, str] | None = None,
    ) -> tuple[dict[str, dict], list[LLMResult]]:
        """Grade every question: objective deterministically, subjective via the marking engine.

        Returns ``(suggestions, subjective_llm_results)``. Marks are always DRAFT suggestions —
        the teacher reviews and can override each one before anything is published (HITL,
        CLAUDE.md §40). The LLM results flow back for metering, not to bill per question.
        """
        rubrics = await fetch_rubrics_for_paper(
            self.db, school_id=school_id, paper_id=exam.source_paper_id
        )
        subject_name = None
        if (
            settings.AEI_V1_MATH_NORMALIZATION_ENABLED
            or settings.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED
            or settings.AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED
        ):
            paper = (
                await self.db.execute(
                    select(QuestionPaper).where(
                        QuestionPaper.id == exam.source_paper_id,
                        QuestionPaper.school_id == school_id,
                    )
                )
            ).scalar_one_or_none()
            subject_name = paper.subject_name if paper and paper.subject_name else None
        suggestions: dict[str, dict] = {}
        subjective_items: list[SubjectiveItem] = []
        subjective_meta: dict[str, dict] = {}
        question_contexts: dict[str, dict] = {}

        for q in exam.question_schema or []:
            qno = str(q["no"])
            max_marks = float(q["max_marks"])
            rubric = rubrics.get(qno, {})
            q_type = str(rubric.get("question_type") or "short")
            answer_key = str(rubric.get("answer_key") or "")
            student_answer = str(student_answers.get(qno, "")).strip()
            options = rubric.get("options")
            topic = q.get("topic") or exam.topic
            question_contexts[qno] = {
                "question_type": q_type,
                "question_text": rubric.get("question_text") or rubric.get("text") or q.get("text"),
                "topic": topic,
                "answer_key": answer_key,
                "rubric": rubric,
                "question": q,
                "checklist": rubric.get("checklist") or q.get("checklist") or [],
                "evaluation_config": rubric.get("evaluation_config") or {},
            }

            if self._is_objective(q_type, answer_key):
                math_result = (
                    evaluate_math_normalization(
                        subject=subject_name,
                        q_type=q_type,
                        student_answer=student_answer,
                        answer_key=answer_key,
                        max_marks=max_marks,
                        rubric=rubric,
                        question=q,
                    )
                    if settings.AEI_V1_MATH_NORMALIZATION_ENABLED
                    else None
                )
                if math_result is not None:
                    suggestion = self._make_suggestion(
                        marks=math_result.marks,
                        max_marks=max_marks,
                        feedback=math_result.feedback,
                        confidence=math_result.confidence,
                        student_answer=student_answer,
                        topic=topic,
                        method=math_result.method,
                        misconception_hint=math_result.misconception_hint,
                    )
                    suggestion.update(math_result.metadata)
                    suggestions[qno] = suggestion
                else:
                    marks, feedback, confidence = grade_objective(
                        q_type=q_type,
                        student_answer=student_answer,
                        answer_key=answer_key,
                        max_marks=max_marks,
                        options=options,
                    )
                    suggestions[qno] = self._make_suggestion(
                        marks=marks,
                        max_marks=max_marks,
                        feedback=feedback,
                        confidence=confidence,
                        student_answer=student_answer,
                        topic=topic,
                        method="objective",
                        misconception_hint=self._misconception_hint(rubric, marks, max_marks),
                    )
            else:
                subjective_items.append(
                    SubjectiveItem(
                        number=qno,
                        question_text=str(rubric.get("question_text") or rubric.get("text") or ""),
                        answer_key=answer_key,
                        max_marks=max_marks,
                        student_answer=student_answer,
                        topic=topic,
                        acceptable_answers=rubric.get("acceptable_answers"),
                    )
                )
                subjective_meta[qno] = {
                    "max_marks": max_marks,
                    "student_answer": student_answer,
                    "topic": topic,
                    "answer_key": answer_key,
                    "rubric": rubric,
                }

        subjective_results: list[LLMResult] = []
        if subjective_items:
            subj_suggestions, subjective_results = await self._grade_subjective_items(
                exam=exam,
                school_id=school_id,
                items=subjective_items,
                meta=subjective_meta,
            )
            suggestions.update(subj_suggestions)

        if settings.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED:
            suggestions = apply_language_ocr_assist_metadata(
                suggestions,
                subject=subject_name,
                answer_sources=answer_sources or {},
            )

        if settings.AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED:
            suggestions = apply_visual_science_assist_metadata(
                suggestions,
                subject=subject_name,
                question_contexts=question_contexts,
            )

        if settings.AEI_V1_REVIEW_POLICY_ENABLED:
            suggestions = apply_review_policy_metadata(suggestions)

        return suggestions, subjective_results

    @staticmethod
    def _misconception_hint(rubric: dict, marks: float, max_marks: float) -> str | None:
        if marks < max_marks and rubric.get("common_wrong_answers"):
            return str(rubric["common_wrong_answers"][0])
        return None

    async def _grade_subjective_items(
        self,
        *,
        exam: Exam,
        school_id: uuid.UUID,
        items: list[SubjectiveItem],
        meta: dict[str, dict],
    ) -> tuple[dict[str, dict], list[LLMResult]]:
        """Mark open-ended answers with the rubric-per-criterion engine; degrade gracefully.

        One grounded gateway call marks the whole batch. If the provider is unconfigured or fails,
        or skips a question, that question falls back to the deterministic token-overlap heuristic
        so a provider outage never blocks a teacher from getting marks to review.
        """
        paper = (
            await self.db.execute(
                select(QuestionPaper).where(
                    QuestionPaper.id == exam.source_paper_id,
                    QuestionPaper.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        board = (paper.board if paper else None) or "SSC"
        grade = (paper.grade if paper else None) or ""
        subject = (paper.subject_name if paper else None) or ""

        eval_topics = sorted({it.topic for it in items if it.topic})
        grounding = await ground_for_evaluation(
            self.db,
            school_id=school_id,
            pack_id=paper.pack_id if paper else None,
            topics=eval_topics or None,
        )

        engine_out: dict[str, dict] = {}
        llm_results: list[LLMResult] = []
        try:
            engine_out, result = await evaluate_subjective(
                items,
                board=board,
                grade=grade,
                subject=subject,
                grounding=grounding if not grounding.is_empty else None,
            )
            llm_results.append(result)
        except Exception:
            # No mark is worse than a heuristic mark the teacher can fix — never fail the sheet.
            logger.warning(
                "subjective_llm_eval_failed_fallback_heuristic",
                exam_id=str(exam.id),
                questions=len(items),
            )

        suggestions: dict[str, dict] = {}
        for item in items:
            m = meta[item.number]
            eng = engine_out.get(item.number)
            if eng is not None:
                citations = [int(n) for n in (eng.get("citations") or []) if str(n).isdigit()]
                grounding_sources = (
                    resolve_citations(grounding.sources, citations)
                    if not grounding.is_empty and citations
                    else []
                )
                suggestions[item.number] = self._make_suggestion(
                    marks=eng["marks_suggested"],
                    max_marks=m["max_marks"],
                    feedback=eng["feedback"],
                    confidence=eng["confidence"],
                    student_answer=m["student_answer"],
                    topic=m["topic"],
                    method="llm_rubric",
                    misconception_hint=self._misconception_hint(
                        m["rubric"], eng["marks_suggested"], m["max_marks"]
                    ),
                    criteria=eng.get("criteria"),
                    missing_concepts=eng.get("missing_concepts"),
                    citations=citations,
                    grounding_sources=grounding_sources,
                    grounded=bool(grounding_sources),
                )
            else:
                marks, feedback, confidence = grade_subjective_heuristic(
                    student_answer=m["student_answer"],
                    answer_key=m["answer_key"],
                    max_marks=m["max_marks"],
                )
                suggestions[item.number] = self._make_suggestion(
                    marks=marks,
                    max_marks=m["max_marks"],
                    feedback=feedback,
                    confidence=confidence,
                    student_answer=m["student_answer"],
                    topic=m["topic"],
                    method="heuristic_fallback",
                    misconception_hint=self._misconception_hint(
                        m["rubric"], marks, m["max_marks"]
                    ),
                )
        return suggestions, llm_results

    async def list_for_exam(
        self, school_id: uuid.UUID, exam_id: uuid.UUID
    ) -> list[AnswerSheetEvaluation]:
        await TenantScope(self.db, school_id).exam(exam_id)
        result = await self.db.execute(
            select(AnswerSheetEvaluation)
            .where(
                AnswerSheetEvaluation.school_id == school_id,
                AnswerSheetEvaluation.exam_id == exam_id,
            )
            .order_by(AnswerSheetEvaluation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_evaluation(
        self, school_id: uuid.UUID, evaluation_id: uuid.UUID
    ) -> AnswerSheetEvaluation | None:
        result = await self.db.execute(
            select(AnswerSheetEvaluation).where(
                AnswerSheetEvaluation.id == evaluation_id,
                AnswerSheetEvaluation.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def approve(
        self,
        *,
        school_id: uuid.UUID,
        evaluation_id: uuid.UUID,
        data: EvaluationApprove,
        approved_by: uuid.UUID,
    ) -> AnswerSheetEvaluation:
        row = (
            await self.db.execute(
                select(AnswerSheetEvaluation)
                .where(
                    AnswerSheetEvaluation.id == evaluation_id,
                    AnswerSheetEvaluation.school_id == school_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not row:
            raise EvalError("Evaluation not found")
        if row.status != EVAL_STATUS_SUGGESTED:
            raise EvalError("Only suggested evaluations can be approved")
        if not row.ai_suggestions:
            raise EvalError("No AI suggestions to approve")

        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(row.exam_id)

        approved_at = datetime.now(timezone.utc)
        teacher_overrides = data.teacher_overrides or {}
        if settings.AEI_V1_REVIEW_POLICY_ENABLED:
            try:
                teacher_overrides = normalize_teacher_overrides_for_review_policy(
                    suggestions=row.ai_suggestions,
                    teacher_overrides=teacher_overrides,
                    reviewer_identifier=str(approved_by),
                    review_timestamp=approved_at,
                )
            except ValueError as exc:
                raise EvalError(str(exc)) from exc
        if settings.AEI_V1_MANUAL_REVIEW_ACK_REQUIRED:
            try:
                teacher_overrides = validate_and_merge_manual_review_acknowledgements(
                    suggestions=row.ai_suggestions,
                    teacher_overrides=teacher_overrides,
                    manual_review_acknowledgements=data.manual_review_acknowledgements,
                    reviewer_identifier=str(approved_by),
                    review_timestamp=approved_at,
                )
            except ValueError as exc:
                raise EvalError(str(exc)) from exc

        question_marks: dict[str, float] = {}
        for qno, suggestion in row.ai_suggestions.items():
            override = teacher_overrides.get(qno) or {}
            marks = override.get("marks")
            if marks is None:
                marks = suggestion.get("marks_suggested", 0)
            max_m = float(suggestion.get("max_marks", 0))
            marks_f = round(float(marks), 2)
            if marks_f < 0 or marks_f > max_m:
                raise EvalError(f"Marks for Q{qno} outside 0..{max_m}")
            question_marks[qno] = marks_f

        row.teacher_overrides = teacher_overrides or None
        row.correction_summary = data.correction_summary or row.correction_summary
        row.status = EVAL_STATUS_APPROVED
        row.approved_by = approved_by
        row.approved_at = approved_at

        exam_service = ExamService(self.db)
        feedback_lines = [
            f"Q{qno}: {(row.ai_suggestions.get(qno) or {}).get('feedback', '')}"
            for qno in sorted(question_marks, key=lambda x: int(x) if x.isdigit() else x)
        ]
        await exam_service.enter_marks(
            school_id,
            row.exam_id,
            [
                MarkEntry(
                    student_id=row.student_id,
                    question_marks=question_marks,
                    remarks=row.correction_summary,
                )
            ],
        )

        mark_row = (
            await self.db.execute(
                select(ExamMark).where(
                    ExamMark.exam_id == row.exam_id,
                    ExamMark.student_id == row.student_id,
                    ExamMark.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if mark_row:
            mark_row.ai_graded = True
            mark_row.ai_feedback = row.correction_summary or "\n".join(feedback_lines[:10])

        await extract_from_evaluation(
            self.db, evaluation=row, exam=exam, approved_by=approved_by
        )

        await self.db.flush()
        return row

    async def list_corrections_history(
        self,
        school_id: uuid.UUID,
        *,
        class_id: uuid.UUID | None = None,
        exam_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
        subject_ids: set[uuid.UUID] | None = None,
        limit: int = 100,
    ) -> list[dict]:
        query = (
            select(AnswerSheetEvaluation, Exam, QuestionPaper)
            .join(Exam, Exam.id == AnswerSheetEvaluation.exam_id)
            .outerjoin(
                QuestionPaper,
                (QuestionPaper.id == Exam.source_paper_id)
                & (QuestionPaper.school_id == school_id),
            )
            .where(
                AnswerSheetEvaluation.school_id == school_id,
                AnswerSheetEvaluation.status == EVAL_STATUS_APPROVED,
            )
        )
        if class_id:
            query = query.where(Exam.class_id == class_id)
        if subject_ids is not None:
            if not subject_ids:
                return []
            query = query.where(Exam.subject_id.in_(subject_ids))
        if exam_id:
            query = query.where(AnswerSheetEvaluation.exam_id == exam_id)
        if student_id:
            query = query.where(AnswerSheetEvaluation.student_id == student_id)

        rows = (
            await self.db.execute(
                query.order_by(AnswerSheetEvaluation.approved_at.desc()).limit(limit)
            )
        ).all()

        history: list[dict] = []
        for ev, exam, paper in rows:
            suggestions = ev.ai_suggestions or {}
            overrides = ev.teacher_overrides or {}
            for qno, suggestion in suggestions.items():
                override = overrides.get(qno) or {}
                ai_marks = float(suggestion.get("marks_suggested", 0))
                teacher_marks = float(override.get("marks", ai_marks))
                citation_ids = [
                    str(src.get("ref_id"))
                    for src in (suggestion.get("grounding_sources") or [])
                    if isinstance(src, dict) and src.get("ref_id")
                ]
                history.append({
                    "evaluation_id": ev.id,
                    "exam_id": exam.id,
                    "question_paper_id": exam.source_paper_id,
                    "curriculum_pack_id": paper.pack_id if paper else None,
                    "question_paper_grounded": bool(paper and paper.grounded),
                    "evaluation_grounded": bool(
                        suggestion.get("grounded") and suggestion.get("grounding_sources")
                    ),
                    "exam_title": exam.title,
                    "student_id": ev.student_id,
                    "question_no": qno,
                    "ai_marks": ai_marks,
                    "teacher_marks": teacher_marks,
                    "max_marks": float(suggestion.get("max_marks", 0)),
                    "ai_feedback": str(suggestion.get("feedback", "")),
                    "override_reason": override.get("reason"),
                    "approved_at": ev.approved_at,
                    "topic": suggestion.get("topic"),
                    "method": suggestion.get("method"),
                    "citation_ids": sorted(set(citation_ids)),
                })
        return history
