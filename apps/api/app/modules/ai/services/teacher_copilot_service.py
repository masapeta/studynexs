"""Teacher Copilot — grounded lesson planning, QP review, and feedback drafting.

All LLM calls go through the shared gateway; curriculum context via ``ground_for_pack``.
Suggestions only — teachers approve or edit before use (HITL).
"""
from __future__ import annotations

import json
import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope, assert_qp_generate
from app.db.models.academic import Class, Subject
from app.db.models.ai_usage import AIUsage
from app.db.models.curriculum_pack import PackStatus
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.db.models.question_paper import QuestionPaper
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.gateway import LLMMessage, LLMResult, generate_llm, record_usage
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits
from app.modules.ai.services.assessment_grounding import (
    GroundingContext,
    ground_for_pack,
    resolve_citations,
)
from app.modules.ai.vectorstore.base import VectorStore
from app.modules.curriculum.services.pack_service import PackError, PackService

logger = structlog.get_logger()


def _build_lesson_plan_messages(
    *,
    board: str,
    grade: str,
    subject: str,
    topic: str,
    chapter: str | None,
    context_text: str,
    source_count: int,
) -> list[LLMMessage]:
    chapter_line = f"Chapter: {chapter}.\n" if chapter else ""
    system = (
        f"You are an expert {board} {grade} {subject} teacher in India. "
        "Create a practical single-period lesson plan grounded ONLY in the CURRICULUM CONTEXT below. "
        "Every segment must cite at least one source number from the context. "
        "Return JSON only."
    )
    user = (
        f"CURRICULUM CONTEXT (numbered sources 1..{source_count} — cite by number):\n"
        f"{context_text}\n\n"
        f"Class: {grade}. Subject: {subject}.\n"
        f"{chapter_line}"
        f"Focus topic: {topic}.\n\n"
        "Return JSON:\n"
        '{"title": str, "segments": ['
        '{"duration_min": int, "activity": str, "citations": [int]}], '
        '"learning_objectives": [str], "notes": str}\n'
        "Provide 4–6 segments totalling about 40 minutes. "
        "Every segment MUST include at least one valid citation."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _build_qp_review_messages(
    *,
    board: str,
    grade: str,
    subject: str,
    paper_title: str,
    sections_json: str,
    context_text: str,
    source_count: int,
) -> list[LLMMessage]:
    system = (
        f"You are an experienced {board} board examiner reviewing a {grade} {subject} "
        "question paper. Use the curriculum context to judge syllabus alignment, clarity, "
        "and difficulty balance. Provide constructive suggestions — do not rewrite the entire paper. "
        "Return JSON only."
    )
    user = (
        f"CURRICULUM CONTEXT (sources 1..{source_count}):\n{context_text}\n\n"
        f"Paper title: {paper_title}\n"
        f"Paper sections (JSON):\n{sections_json}\n\n"
        "Return JSON:\n"
        '{"summary": str, "overall_quality": str (good | needs_work), '
        '"suggestions": [{"section_title": str, "question_number": str | null, '
        '"issue": str, "suggestion": str, "citations": [int]}]}'
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _build_feedback_messages(
    *,
    board: str,
    grade: str,
    subject: str,
    topic: str,
    student_answer: str,
    rubric: str | None,
    context_text: str,
    source_count: int,
) -> list[LLMMessage]:
    rubric_line = f"Rubric / marking guide:\n{rubric}\n\n" if rubric else ""
    system = (
        f"You are a supportive {board} {grade} {subject} teacher drafting feedback for a student. "
        "Ground comments in the curriculum context where relevant. Be constructive and specific. "
        "This is a DRAFT for teacher review — not final grades. Return JSON only."
    )
    user = (
        f"CURRICULUM CONTEXT (sources 1..{source_count}):\n{context_text}\n\n"
        f"Topic: {topic}.\n"
        f"{rubric_line}"
        f"Student answer:\n{student_answer}\n\n"
        "Return JSON:\n"
        '{"feedback_draft": str, "strengths": [str], "improvements": [str], '
        '"citations": [int], "tone": "constructive"}'
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _normalize_lesson_segments(raw: list, sources: list[dict]) -> list[dict]:
    out: list[dict] = []
    max_idx = len(sources)
    for seg in raw or []:
        if not isinstance(seg, dict):
            continue
        activity = str(seg.get("activity") or "").strip()
        if not activity:
            continue
        try:
            duration = int(seg.get("duration_min") or 5)
        except (TypeError, ValueError):
            duration = 5
        citations = []
        for c in seg.get("citations") or []:
            try:
                idx = int(c)
                if 1 <= idx <= max_idx:
                    citations.append(idx)
            except (TypeError, ValueError):
                continue
        row: dict = {"duration_min": max(1, min(duration, 60)), "activity": activity}
        if citations:
            row["citations"] = citations
            row["citation_sources"] = resolve_citations(sources, citations)
        out.append(row)
    return out or [
        {"duration_min": 10, "activity": "Review curriculum context and objectives"},
    ]


async def _record_copilot_usage(
    db: AsyncSession,
    *,
    feature: str,
    result: LLMResult,
    reserved_row: AIUsage | None,
    ref_type: str,
    ref_id: uuid.UUID | None = None,
) -> AIUsage | None:
    if not reserved_row:
        return None
    return await record_usage(
        db,
        feature=feature,
        result=result,
        reserved_row=reserved_row,
        ref_type=ref_type,
        ref_id=ref_id,
    )


async def _resolve_grounding(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    topics: list[str] | None,
    embedder: EmbeddingService | None,
    store: VectorStore | None,
) -> tuple[GroundingContext, object]:
    try:
        pack = await PackService(db).get_pack(school_id, pack_id)
    except PackError as exc:
        raise ValueError(str(exc)) from exc
    if pack.class_id != class_id or pack.subject_id != subject_id:
        raise ValueError("Curriculum pack does not match this class and subject.")
    if pack.status != PackStatus.APPROVED:
        raise ValueError(
            "Approve the curriculum pack before using Teacher Copilot with it."
        )
    grounding = await ground_for_pack(
        db, pack=pack, topics=topics, embedder=embedder, store=store
    )
    if grounding.is_empty:
        raise ValueError(
            "This curriculum pack has no chapters/topics to ground on yet. "
            "Add curriculum content first."
        )
    return grounding, pack


class TeacherCopilotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_grounded_lesson_plan(
        self,
        school_id: uuid.UUID,
        scope: StaffScope,
        *,
        class_id: uuid.UUID,
        subject_id: uuid.UUID,
        pack_id: uuid.UUID,
        topic: str | None = None,
        chapter: str | None = None,
        scheduled_for: date | None = None,
        created_by: uuid.UUID,
        role: str = "teacher",
        credits_charged: int | None = None,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> LessonPlan:
        assert_qp_generate(scope, class_id, subject_id)
        cls = (
            await self.db.execute(
                select(Class).where(Class.id == class_id, Class.school_id == school_id)
            )
        ).scalar_one_or_none()
        subj = (
            await self.db.execute(
                select(Subject).where(
                    Subject.id == subject_id, Subject.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if not cls or not subj:
            raise ValueError("Class or subject not found")

        focus_topic = (topic or subj.name).strip()
        grounding, pack = await _resolve_grounding(
            self.db,
            school_id=school_id,
            pack_id=pack_id,
            class_id=class_id,
            subject_id=subject_id,
            topics=[focus_topic] if focus_topic else None,
            embedder=embedder,
            store=store,
        )

        from app.db.models.school import School

        school = (await self.db.execute(select(School).where(School.id == school_id))).scalar_one()
        board = pack.board or school.board or "SSC"
        chapter_name = chapter or focus_topic

        messages = _build_lesson_plan_messages(
            board=board,
            grade=cls.grade,
            subject=subj.name,
            topic=focus_topic,
            chapter=chapter_name,
            context_text=grounding.context_text,
            source_count=grounding.chunk_count,
        )

        purpose_tag = "lesson_plan"
        cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
        reserved: AIUsage | None = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=created_by,
                role=role,
                purpose_tag=purpose_tag,
                feature="teacher_copilot",
                credits=cost,
                ref_type="lesson_plan",
            )

        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=4000,
            temperature=0.35,
            feature="teacher_copilot",
            caller="generate_grounded_lesson_plan",
        )

        try:
            data = json.loads(result.text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("lesson_plan_parse_failed", error=str(exc))
            raise ValueError(
                "The AI returned an unreadable lesson plan. Please try again."
            ) from exc

        segments = _normalize_lesson_segments(
            data.get("segments") or [], grounding.sources
        )
        objectives = data.get("learning_objectives") or []
        notes_parts = [str(data.get("notes") or "").strip()]
        if objectives:
            notes_parts.append(
                "Learning objectives:\n" + "\n".join(f"• {o}" for o in objectives[:8])
            )
        notes = "\n\n".join(p for p in notes_parts if p) or None

        sched = scheduled_for or (date.today() + timedelta(days=1))
        title = str(data.get("title") or "").strip() or (
            f"{cls.grade} {cls.section} — {subj.name}: {focus_topic}"
        )

        plan = LessonPlan(
            school_id=school_id,
            class_id=class_id,
            subject_id=subject_id,
            created_by=created_by,
            title=title[:200],
            chapter=chapter_name,
            topic=focus_topic,
            scheduled_for=sched,
            segments=segments,
            status=LessonPlanStatus.DRAFT,
            ai_model=result.model,
            notes=notes,
            pack_id=pack.id,
            grounded=True,
            grounding_sources=grounding.sources,
        )
        self.db.add(plan)
        await self.db.flush()
        await _record_copilot_usage(
            self.db,
            feature="teacher_copilot",
            result=result,
            reserved_row=reserved,
            ref_type="lesson_plan",
            ref_id=plan.id,
        )
        return plan

    async def review_question_paper(
        self,
        school_id: uuid.UUID,
        *,
        paper: QuestionPaper,
        user_id: uuid.UUID,
        role: str = "teacher",
        credits_charged: int | None = None,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> dict:
        if paper.school_id != school_id:
            raise ValueError("Question paper not found")
        if not paper.pack_id:
            raise ValueError(
                "Only curriculum-grounded question papers can be reviewed by Teacher Copilot."
            )

        grounding, pack = await _resolve_grounding(
            self.db,
            school_id=school_id,
            pack_id=paper.pack_id,
            class_id=paper.class_id,
            subject_id=paper.subject_id,
            topics=list(paper.topics or []),
            embedder=embedder,
            store=store,
        )

        sections_json = json.dumps(paper.sections or [], ensure_ascii=False)[:12000]
        messages = _build_qp_review_messages(
            board=paper.board or pack.board or "SSC",
            grade=paper.grade or "",
            subject=paper.subject_name or "",
            paper_title=paper.title,
            sections_json=sections_json,
            context_text=grounding.context_text,
            source_count=grounding.chunk_count,
        )

        purpose_tag = "quality_check"
        cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
        reserved: AIUsage | None = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=user_id,
                role=role,
                purpose_tag=purpose_tag,
                feature="teacher_copilot_review",
                credits=cost,
                ref_type="question_paper",
                ref_id=paper.id,
            )

        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=3000,
            temperature=0.3,
            feature="teacher_copilot_review",
            caller="review_question_paper",
        )

        try:
            data = json.loads(result.text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("qp_review_parse_failed", error=str(exc))
            raise ValueError(
                "The AI returned an unreadable review. Please try again."
            ) from exc

        await _record_copilot_usage(
            self.db,
            feature="teacher_copilot_review",
            result=result,
            reserved_row=reserved,
            ref_type="question_paper",
            ref_id=paper.id,
        )

        suggestions = data.get("suggestions") or []
        if isinstance(suggestions, list):
            for item in suggestions:
                if isinstance(item, dict) and item.get("citations"):
                    item["citation_sources"] = resolve_citations(
                        grounding.sources, item["citations"]
                    )

        return {
            "paper_id": str(paper.id),
            "summary": str(data.get("summary") or ""),
            "overall_quality": str(data.get("overall_quality") or "needs_work"),
            "suggestions": suggestions if isinstance(suggestions, list) else [],
            "grounding_sources": grounding.sources,
            "model": result.model,
        }

    async def draft_feedback(
        self,
        school_id: uuid.UUID,
        *,
        class_id: uuid.UUID,
        subject_id: uuid.UUID,
        pack_id: uuid.UUID,
        topic: str,
        student_answer: str,
        rubric: str | None,
        user_id: uuid.UUID,
        role: str = "teacher",
        credits_charged: int | None = None,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> dict:
        if not student_answer.strip():
            raise ValueError("Student answer is required.")
        if len(student_answer) > 8000:
            raise ValueError("Student answer is too long (max 8000 characters).")

        cls = (
            await self.db.execute(
                select(Class).where(Class.id == class_id, Class.school_id == school_id)
            )
        ).scalar_one_or_none()
        subj = (
            await self.db.execute(
                select(Subject).where(
                    Subject.id == subject_id, Subject.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if not cls or not subj:
            raise ValueError("Class or subject not found")

        grounding, pack = await _resolve_grounding(
            self.db,
            school_id=school_id,
            pack_id=pack_id,
            class_id=class_id,
            subject_id=subject_id,
            topics=[topic],
            embedder=embedder,
            store=store,
        )

        from app.db.models.school import School

        school = (await self.db.execute(select(School).where(School.id == school_id))).scalar_one()
        board = pack.board or school.board or "SSC"

        messages = _build_feedback_messages(
            board=board,
            grade=cls.grade,
            subject=subj.name,
            topic=topic,
            student_answer=student_answer.strip(),
            rubric=rubric,
            context_text=grounding.context_text,
            source_count=grounding.chunk_count,
        )

        purpose_tag = "feedback_draft"
        cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
        reserved: AIUsage | None = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=user_id,
                role=role,
                purpose_tag=purpose_tag,
                feature="teacher_copilot_feedback",
                credits=cost,
            )

        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=2000,
            temperature=0.4,
            feature="teacher_copilot_feedback",
            caller="draft_feedback",
        )

        try:
            data = json.loads(result.text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("feedback_draft_parse_failed", error=str(exc))
            raise ValueError(
                "The AI returned unreadable feedback. Please try again."
            ) from exc

        citations = data.get("citations") or []
        citation_sources = (
            resolve_citations(grounding.sources, citations)
            if isinstance(citations, list)
            else []
        )

        await _record_copilot_usage(
            self.db,
            feature="teacher_copilot_feedback",
            result=result,
            reserved_row=reserved,
            ref_type="teacher_copilot_feedback",
        )

        return {
            "feedback_draft": str(data.get("feedback_draft") or ""),
            "strengths": data.get("strengths") or [],
            "improvements": data.get("improvements") or [],
            "citations": citations,
            "citation_sources": citation_sources,
            "grounding_sources": grounding.sources,
            "tone": str(data.get("tone") or "constructive"),
            "model": result.model,
        }
