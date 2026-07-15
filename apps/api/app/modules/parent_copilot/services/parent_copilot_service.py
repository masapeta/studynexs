"""Parent Copilot — grounded briefings and Q&A for parents (Batch 27).

Uses mastery data, weak-concept graph, teacher-approved narratives, and hybrid RAG.
Prompts minimize PII — refer to \"your child\" rather than names (DPDP-aware).
"""
from __future__ import annotations

import json
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.gateway import LLMMessage, generate_llm, record_usage
from app.modules.ai.gateway.input_guard import sanitize_prompt_text
from app.modules.ai.gateway.output_guard import sanitize_llm_plain_text
from app.modules.ai.rag import HybridRetrievalOptions, HybridRetrievalService, RagService
from app.modules.ai.rag.service import RagService as RagSvc
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits
from app.modules.ai.vectorstore.base import VectorStore
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)
from app.modules.parent_copilot.schemas.copilot import (
    ParentAnswerOut,
    ParentAskIn,
    ParentBriefingOut,
    ParentFocusAreaOut,
)
from app.modules.portal.services.portal_service import parent_child_progress

logger = structlog.get_logger()

_WEAK_THRESHOLD = 70.0


def _build_briefing_messages(
    *,
    board: str,
    grade: str,
    weak_lines: str,
    feedback_lines: str,
    curriculum_context: str,
) -> list[LLMMessage]:
    system = (
        f"You are a supportive school advisor for parents of Class {grade} {board} students in India. "
        "Write a brief progress summary using ONLY the data below. Be warm and practical. "
        "Do not invent marks, ranks, or events. Never use the child's name. "
        "Return JSON only."
    )
    user = (
        f"WEAK TOPICS / CONCEPTS:\n{weak_lines or '(none recorded yet)'}\n\n"
        f"TEACHER FEEDBACK (already approved for parents):\n{feedback_lines or '(none yet)'}\n\n"
        f"CURRICULUM CONTEXT (for home practice alignment):\n"
        f"{curriculum_context or '(not indexed)'}\n\n"
        "Return JSON:\n"
        '{"summary": str, "focus_areas": [{"topic": str, "subject_name": str, '
        '"mastery_pct": number | null, "concept_slug": str | null}], '
        '"home_tips": [str], "encouragement": str}\n'
        "summary under 80 words; 2-4 home_tips; encouragement one sentence."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


def _build_ask_messages(
    *,
    board: str,
    grade: str,
    question: str,
    weak_lines: str,
    curriculum_context: str,
) -> list[LLMMessage]:
    system = (
        f"You are a helpful advisor for parents of a Class {grade} {board} student. "
        "Answer using ONLY the progress data and curriculum context below. "
        "Suggest practical home support — never grade or blame. Return JSON only."
    )
    user = (
        f"PROGRESS DATA:\n{weak_lines or '(no weak topics yet)'}\n\n"
        f"CURRICULUM CONTEXT:\n{curriculum_context or '(not indexed)'}\n\n"
        f"Parent question:\n{question}\n\n"
        'Return JSON: {"answer": str, "home_tips": [str]}\n'
        "Keep answer under 100 words."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


class ParentCopilotService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.weak = StudentWeakConceptService(db)

    async def _student(
        self, *, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> Student | None:
        return (
            await self.db.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.school_id == school_id,
                )
            )
        ).scalar_one_or_none()

    async def _progress_snapshot(
        self,
        *,
        school_id: uuid.UUID,
        parent_user_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> tuple[str, list[ParentFocusAreaOut], str]:
        """Weak topics + teacher feedback lines for prompts (no child name)."""
        progress = await parent_child_progress(
            self.db,
            school_id=school_id,
            parent_user_id=parent_user_id,
            student_id=student_id,
        )
        focus: list[ParentFocusAreaOut] = []
        weak_lines: list[str] = []
        if progress:
            for wt in progress.weak_topics[:6]:
                line = f"- {wt.subject_name}: {wt.topic_display} ({wt.mastery_pct:.0f}% mastery)"
                weak_lines.append(line)
                focus.append(
                    ParentFocusAreaOut(
                        topic=wt.topic_display,
                        subject_name=wt.subject_name,
                        mastery_pct=wt.mastery_pct,
                    )
                )
            for fb in progress.feedbacks[:3]:
                excerpt = (fb.narrative or "")[:200]
                weak_lines.append(f"- Teacher note on {fb.subject_name} / {fb.topic_display}: {excerpt}")

        pairs = await self.weak.get_weak_concepts_for_student(
            school_id=school_id, student_id=student_id
        )
        concept_slugs: dict[str, str] = {}
        for concept, meta in pairs[:6]:
            pct = meta.get("mastery_pct") if meta else None
            weak_lines.append(
                f"- Concept gap: {concept.title} ({pct:.0f}% mastery)" if pct is not None
                else f"- Concept gap: {concept.title}"
            )
            concept_slugs[concept.title.casefold()] = concept.slug
            if not any(f.topic == concept.title for f in focus):
                focus.append(
                    ParentFocusAreaOut(
                        topic=concept.title,
                        subject_name="Curriculum",
                        mastery_pct=float(pct) if pct is not None else None,
                        concept_slug=concept.slug,
                    )
                )

        feedback_lines = ""
        if progress and progress.feedbacks:
            feedback_lines = "\n".join(
                f"- {fb.subject_name} / {fb.topic_display}: {(fb.narrative or '')[:180]}"
                for fb in progress.feedbacks[:3]
            )

        return "\n".join(weak_lines), focus[:6], feedback_lines

    async def _curriculum_context(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        query: str,
        embedder: EmbeddingService | None,
        store: VectorStore | None,
    ) -> tuple[str, uuid.UUID | None, uuid.UUID | None]:
        pairs = await self.weak.get_weak_concepts_for_student(
            school_id=school_id, student_id=student_id
        )
        if not pairs:
            return "", None, None
        concept, _meta = pairs[0]
        rag = RagService(self.db, embedder=embedder, store=store)
        hybrid = HybridRetrievalService(self.db, rag)
        chunks = await hybrid.retrieve_hybrid(
            query,
            school_id=school_id,
            pack_id=concept.pack_id,
            top_k=4,
            options=HybridRetrievalOptions(
                concept_ids=[concept.id],
                student_id=student_id,
                rerank=True,
            ),
        )
        return RagSvc.build_context(chunks), concept.pack_id, concept.id

    async def generate_briefing(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
        credits_charged: int | None = None,
    ) -> ParentBriefingOut:
        student = await self._student(school_id=school_id, student_id=student_id)
        if student is None:
            raise ValueError("Student not found")

        cls = (
            await self.db.execute(
                select(Class).where(Class.id == student.class_id, Class.school_id == school_id)
            )
        ).scalar_one_or_none()
        school = (
            await self.db.execute(select(School).where(School.id == school_id))
        ).scalar_one()
        grade = cls.grade if cls else "10"
        board = school.board or "SSC"

        weak_lines, focus_areas, feedback_lines = await self._progress_snapshot(
            school_id=school_id,
            parent_user_id=user_id,
            student_id=student_id,
        )
        primary_query = focus_areas[0].topic if focus_areas else "curriculum topics"
        curriculum_context, _, _ = await self._curriculum_context(
            school_id=school_id,
            student_id=student_id,
            query=primary_query,
            embedder=embedder,
            store=store,
        )

        messages = _build_briefing_messages(
            board=board,
            grade=grade,
            weak_lines=weak_lines,
            feedback_lines=feedback_lines,
            curriculum_context=curriculum_context,
        )

        purpose_tag = "parent_briefing"
        cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
        reserved = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=user_id,
                role=role,
                purpose_tag=purpose_tag,
                feature="parent_copilot",
                credits=cost,
                ref_type="parent_copilot_briefing",
            )

        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=900,
            temperature=0.35,
            feature="parent_copilot",
            caller="generate_briefing",
        )
        await record_usage(
            self.db,
            feature="parent_copilot",
            result=result,
            reserved_row=reserved,
            ref_type="parent_copilot_briefing",
            ref_id=student_id,
        )

        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise ValueError("Copilot returned invalid JSON") from exc

        summary = sanitize_llm_plain_text(str(payload.get("summary", "")), max_length=600)
        if not summary:
            raise ValueError("Copilot returned an empty briefing")

        tips_raw = payload.get("home_tips") or []
        home_tips = [
            sanitize_llm_plain_text(str(t), max_length=200)
            for t in tips_raw[:4]
            if sanitize_llm_plain_text(str(t), max_length=200)
        ]
        encouragement = sanitize_llm_plain_text(
            str(payload.get("encouragement", "")), max_length=300
        )

        llm_focus = payload.get("focus_areas") or []
        if isinstance(llm_focus, list) and llm_focus and not focus_areas:
            for item in llm_focus[:6]:
                if isinstance(item, dict):
                    focus_areas.append(
                        ParentFocusAreaOut(
                            topic=str(item.get("topic", "")),
                            subject_name=str(item.get("subject_name", "—")),
                            mastery_pct=item.get("mastery_pct"),
                            concept_slug=item.get("concept_slug"),
                        )
                    )

        return ParentBriefingOut(
            student_id=student_id,
            summary=summary,
            focus_areas=focus_areas,
            home_tips=home_tips,
            encouragement=encouragement,
            grounded=bool(curriculum_context or weak_lines),
            model=result.model,
        )

    async def ask(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        body: ParentAskIn,
        user_id: uuid.UUID,
        role: str,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
        credits_charged: int | None = None,
    ) -> ParentAnswerOut:
        student = await self._student(school_id=school_id, student_id=student_id)
        if student is None:
            raise ValueError("Student not found")

        question = sanitize_prompt_text(
            body.question.strip(),
            max_length=800,
            field_name="question",
            reject_injection=True,
        )
        if not question:
            raise ValueError("Question is required")

        cls = (
            await self.db.execute(
                select(Class).where(Class.id == student.class_id, Class.school_id == school_id)
            )
        ).scalar_one_or_none()
        school = (
            await self.db.execute(select(School).where(School.id == school_id))
        ).scalar_one()
        grade = cls.grade if cls else "10"
        board = school.board or "SSC"

        weak_lines, _, _ = await self._progress_snapshot(
            school_id=school_id,
            parent_user_id=user_id,
            student_id=student_id,
        )
        curriculum_context, _, _ = await self._curriculum_context(
            school_id=school_id,
            student_id=student_id,
            query=question,
            embedder=embedder,
            store=store,
        )

        messages = _build_ask_messages(
            board=board,
            grade=grade,
            question=question,
            weak_lines=weak_lines,
            curriculum_context=curriculum_context,
        )

        purpose_tag = "parent_ask"
        cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
        reserved = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=user_id,
                role=role,
                purpose_tag=purpose_tag,
                feature="parent_copilot",
                credits=cost,
                ref_type="parent_copilot_ask",
            )

        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=700,
            temperature=0.35,
            feature="parent_copilot",
            caller="parent_ask",
        )
        await record_usage(
            self.db,
            feature="parent_copilot",
            result=result,
            reserved_row=reserved,
            ref_type="parent_copilot_ask",
            ref_id=student_id,
        )

        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise ValueError("Copilot returned invalid JSON") from exc

        answer = sanitize_llm_plain_text(str(payload.get("answer", "")), max_length=1000)
        if not answer:
            raise ValueError("Copilot returned an empty answer")

        tips_raw = payload.get("home_tips") or []
        home_tips = [
            sanitize_llm_plain_text(str(t), max_length=200)
            for t in tips_raw[:3]
            if sanitize_llm_plain_text(str(t), max_length=200)
        ]

        return ParentAnswerOut(
            answer=answer,
            home_tips=home_tips,
            grounded=bool(curriculum_context or weak_lines),
            model=result.model,
        )
