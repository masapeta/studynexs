"""Parent Copilot — grounded briefings and Q&A for parents (Batch 27).

Uses mastery data, weak-concept graph, teacher-approved narratives, and hybrid RAG.
Prompts minimize PII — refer to \"your child\" rather than names (DPDP-aware).
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.misconception import MisconceptionEntry
from app.db.models.school import School
from app.db.models.student import Student
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


@dataclass(frozen=True)
class ParentEvidence:
    """Internal certification metadata for parent-facing guidance.

    Parent UI renders this as plain-language "why" copy; runtime proofs use the
    identifiers to verify same-pack grounding without exposing raw ledger jargon.
    """

    curriculum_context: str = ""
    pack_id: uuid.UUID | None = None
    concept_id: uuid.UUID | None = None
    concept_slug: str | None = None
    concept_title: str | None = None
    mastery_topic: str | None = None
    mastery_pct: float | None = None
    source_count: int = 0


def _has_certified_parent_evidence(evidence: ParentEvidence) -> bool:
    return bool(evidence.pack_id and evidence.concept_id and evidence.source_count > 0)


def _parent_evidence_reason(
    *, focus_areas: list[ParentFocusAreaOut], evidence: ParentEvidence
) -> str:
    primary = focus_areas[0] if focus_areas else None
    topic = evidence.mastery_topic or evidence.concept_title or (primary.topic if primary else "")
    subject = (
        primary.subject_name
        if primary and primary.subject_name != "Curriculum"
        else "this subject"
    )
    if evidence.mastery_pct is not None and topic:
        return (
            f"Based on your child's recent {subject} assessment, mastery is "
            f"{evidence.mastery_pct:.0f}% on {topic}, below the learning target."
        )
    if topic:
        return (
            f"Based on your child's recent learning evidence, {topic} is the current "
            "focus area."
        )
    return "Based on your child's latest learning evidence in StudyNexs."


def _parent_evidence_summary(evidence: ParentEvidence) -> str:
    if _has_certified_parent_evidence(evidence):
        return (
            "Verified from approved school curriculum and recent learning evidence "
            f"({evidence.source_count} source"
            f"{'s' if evidence.source_count != 1 else ''})."
        )
    return (
        "Progress evidence is available, but approved curriculum grounding was not "
        "verified for this response."
    )


def _build_briefing_messages(
    *,
    board: str,
    grade: str,
    weak_lines: str,
    feedback_lines: str,
    curriculum_context: str,
) -> list[LLMMessage]:
    system = (
        f"You are a supportive school advisor for parents of Class {grade} "
        f"{board} students in India. "
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

    async def _exam_focus_from_misconceptions(
        self, *, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> tuple[list[ParentFocusAreaOut], list[str]]:
        """Recent exam-derived topics (same chain as tutor recommendations)."""
        rows = (
            await self.db.execute(
                select(MisconceptionEntry, Subject.name)
                .join(Subject, Subject.id == MisconceptionEntry.subject_id)
                .where(
                    MisconceptionEntry.school_id == school_id,
                    MisconceptionEntry.student_id == student_id,
                    Subject.school_id == school_id,
                )
                .order_by(MisconceptionEntry.created_at.desc())
                .limit(4)
            )
        ).all()
        focus: list[ParentFocusAreaOut] = []
        lines: list[str] = []
        for mc, subject_name in rows:
            topic = (mc.topic or "General").strip()
            if not topic or any(f.topic == topic for f in focus):
                continue
            mistake = (mc.common_mistake or "review this concept")[:120]
            lines.append(f"- Recent exam ({subject_name} / {topic}): {mistake}")
            focus.append(
                ParentFocusAreaOut(
                    topic=topic,
                    subject_name=subject_name,
                    mastery_pct=None,
                    evidence_reason="Recent assessment misconception",
                )
            )
        return focus, lines

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
        exam_focus, exam_lines = await self._exam_focus_from_misconceptions(
            school_id=school_id, student_id=student_id
        )
        focus.extend(exam_focus)
        weak_lines.extend(exam_lines)
        if progress:
            for wt in progress.weak_topics[:6]:
                if any(f.topic == wt.topic_display for f in focus):
                    continue
                line = f"- {wt.subject_name}: {wt.topic_display} ({wt.mastery_pct:.0f}% mastery)"
                weak_lines.append(line)
                focus.append(
                    ParentFocusAreaOut(
                        topic=wt.topic_display,
                        subject_name=wt.subject_name,
                        mastery_pct=wt.mastery_pct,
                        evidence_reason="Mastery below target from recent assessments",
                    )
                )
            for fb in progress.feedbacks[:3]:
                excerpt = (fb.narrative or "")[:200]
                weak_lines.append(
                    f"- Teacher note on {fb.subject_name} / {fb.topic_display}: {excerpt}"
                )

        pairs = await self.weak.get_weak_concepts_for_student(
            school_id=school_id, student_id=student_id
        )
        for concept, meta in pairs[:6]:
            pct = meta.get("mastery_pct") if meta else None
            mastery_topic = str(meta.get("topic") or concept.title) if meta else concept.title
            weak_lines.append(
                f"- Concept gap: {concept.title} ({pct:.0f}% mastery)" if pct is not None
                else f"- Concept gap: {concept.title}"
            )
            existing = next(
                (
                    item
                    for item in focus
                    if item.topic.casefold() in {concept.title.casefold(), mastery_topic.casefold()}
                ),
                None,
            )
            if existing:
                existing.concept_slug = existing.concept_slug or concept.slug
                existing.pack_id = existing.pack_id or concept.pack_id
                existing.concept_id = existing.concept_id or concept.id
                if existing.mastery_pct is None and pct is not None:
                    existing.mastery_pct = float(pct)
                if not existing.evidence_reason:
                    existing.evidence_reason = "Mapped to approved curriculum evidence"
            else:
                focus.append(
                    ParentFocusAreaOut(
                        topic=concept.title,
                        subject_name="Curriculum",
                        mastery_pct=float(pct) if pct is not None else None,
                        concept_slug=concept.slug,
                        pack_id=concept.pack_id,
                        concept_id=concept.id,
                        evidence_reason="Mapped to approved curriculum evidence",
                    )
                )

        feedback_lines = ""
        if progress and progress.feedbacks:
            feedback_lines = "\n".join(
                f"- {fb.subject_name} / {fb.topic_display}: {(fb.narrative or '')[:180]}"
                for fb in progress.feedbacks[:3]
            )

        return "\n".join(weak_lines), focus[:6], feedback_lines

    def _deterministic_briefing(
        self,
        *,
        student_id: uuid.UUID,
        grade: str,
        focus_areas: list[ParentFocusAreaOut],
        weak_lines: str,
        attendance_pct: float | None,
        evidence: ParentEvidence,
    ) -> ParentBriefingOut:
        """Progress-based summary when the LLM is unavailable or returns empty (demo-safe)."""
        if focus_areas:
            topics = ", ".join(f"{f.subject_name} ({f.topic})" for f in focus_areas[:3])
            summary = (
                f"Your Class {grade} child is strengthening {topics}. "
                "These topics came from recent assessments — short, regular practice "
                "at home helps most."
            )
            home_tips = [
                "Ask your child to walk through one solved example aloud each evening.",
                "Keep revision to 20 minutes — consistency matters more than long sessions.",
            ]
        else:
            summary = (
                f"Your Class {grade} child is progressing this term. "
                "Watch attendance and class-work notices for what to revise at home."
            )
            home_tips = [
                "Check school notices for this week's class work and due dates.",
                "Encourage your child to note one doubt after each Maths period.",
            ]
        if attendance_pct is not None and attendance_pct < 85:
            summary += (
                f" Attendance is {attendance_pct:.0f}% — being present supports "
                "steady progress."
            )

        return ParentBriefingOut(
            student_id=student_id,
            summary=summary,
            focus_areas=focus_areas,
            home_tips=home_tips,
            encouragement=(
                "Steady support at home — even a few minutes daily — makes a "
                "visible difference."
            ),
            pack_id=evidence.pack_id,
            concept_id=evidence.concept_id,
            concept_slug=evidence.concept_slug,
            mastery_topic=evidence.mastery_topic,
            source_count=evidence.source_count,
            grounded=_has_certified_parent_evidence(evidence),
            fallback=True,
            evidence_reason=_parent_evidence_reason(
                focus_areas=focus_areas, evidence=evidence
            ),
            evidence_summary=_parent_evidence_summary(evidence),
            model="deterministic",
        )

    def _deterministic_ask(
        self,
        *,
        question: str,
        focus_areas: list[ParentFocusAreaOut],
        weak_lines: str,
        grade: str,
        evidence: ParentEvidence,
    ) -> ParentAnswerOut:
        q = question.casefold()
        if focus_areas and ("math" in q or "maths" in q or "week" in q or "summar" in q):
            primary = focus_areas[0]
            answer = (
                f"This week in {primary.subject_name}, focus on {primary.topic}. "
                f"Your Class {grade} child's teachers flagged this from recent work — "
                "review the class-work notice and ask them to explain one practice problem."
            )
            home_tips = [
                f"Spend 15 minutes on {primary.topic} — use the textbook examples, "
                "not new material.",
                "Celebrate effort on attempted problems, not only correct answers.",
            ]
        elif focus_areas:
            primary = focus_areas[0]
            answer = (
                f"Recent assessments suggest attention on {primary.subject_name}: {primary.topic}. "
                "Ask your child's teacher if a short remedial worksheet is available."
            )
            home_tips = ["Check notices for assigned class work this week."]
        else:
            answer = (
                "Your child's class work and notices are the best guide for this week. "
                "Open the notices section and review any Maths assignments together."
            )
            home_tips = ["Maintain regular study time even when there are no upcoming tests."]

        return ParentAnswerOut(
            answer=answer,
            home_tips=home_tips,
            pack_id=evidence.pack_id,
            concept_id=evidence.concept_id,
            concept_slug=evidence.concept_slug,
            mastery_topic=evidence.mastery_topic,
            source_count=evidence.source_count,
            grounded=_has_certified_parent_evidence(evidence),
            fallback=True,
            evidence_reason=_parent_evidence_reason(
                focus_areas=focus_areas, evidence=evidence
            ),
            evidence_summary=_parent_evidence_summary(evidence),
            model="deterministic",
        )

    async def _curriculum_context(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        query: str,
        embedder: EmbeddingService | None,
        store: VectorStore | None,
    ) -> ParentEvidence:
        pairs = await self.weak.get_weak_concepts_for_student(
            school_id=school_id, student_id=student_id
        )
        if not pairs:
            return ParentEvidence()
        concept, meta = pairs[0]
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
        mastery_pct = None
        mastery_topic = concept.title
        if meta:
            mastery_topic = str(meta.get("topic") or concept.title)
            if meta.get("mastery_pct") is not None:
                mastery_pct = float(meta["mastery_pct"])
        return ParentEvidence(
            curriculum_context=RagSvc.build_context(chunks),
            pack_id=concept.pack_id,
            concept_id=concept.id,
            concept_slug=concept.slug,
            concept_title=concept.title,
            mastery_topic=mastery_topic,
            mastery_pct=mastery_pct,
            source_count=len(chunks),
        )

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

        progress = await parent_child_progress(
            self.db,
            school_id=school_id,
            parent_user_id=user_id,
            student_id=student_id,
        )

        weak_lines, focus_areas, feedback_lines = await self._progress_snapshot(
            school_id=school_id,
            parent_user_id=user_id,
            student_id=student_id,
        )
        primary_query = focus_areas[0].topic if focus_areas else "curriculum topics"
        evidence = await self._curriculum_context(
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
            curriculum_context=evidence.curriculum_context,
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
        except json.JSONDecodeError:
            return self._deterministic_briefing(
                student_id=student_id,
                grade=grade,
                focus_areas=focus_areas,
                weak_lines=weak_lines,
                attendance_pct=progress.attendance_pct if progress else None,
                evidence=evidence,
            )

        summary = sanitize_llm_plain_text(str(payload.get("summary", "")), max_length=600)
        if not summary:
            return self._deterministic_briefing(
                student_id=student_id,
                grade=grade,
                focus_areas=focus_areas,
                weak_lines=weak_lines,
                attendance_pct=progress.attendance_pct if progress else None,
                evidence=evidence,
            )

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
            pack_id=evidence.pack_id,
            concept_id=evidence.concept_id,
            concept_slug=evidence.concept_slug,
            mastery_topic=evidence.mastery_topic,
            source_count=evidence.source_count,
            grounded=_has_certified_parent_evidence(evidence),
            fallback=False,
            evidence_reason=_parent_evidence_reason(
                focus_areas=focus_areas, evidence=evidence
            ),
            evidence_summary=_parent_evidence_summary(evidence),
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

        weak_lines, focus_areas, _ = await self._progress_snapshot(
            school_id=school_id,
            parent_user_id=user_id,
            student_id=student_id,
        )
        evidence = await self._curriculum_context(
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
            curriculum_context=evidence.curriculum_context,
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
        except json.JSONDecodeError:
            return self._deterministic_ask(
                question=question,
                focus_areas=focus_areas,
                weak_lines=weak_lines,
                grade=grade,
                evidence=evidence,
            )

        answer = sanitize_llm_plain_text(str(payload.get("answer", "")), max_length=1000)
        if not answer:
            return self._deterministic_ask(
                question=question,
                focus_areas=focus_areas,
                weak_lines=weak_lines,
                grade=grade,
                evidence=evidence,
            )

        tips_raw = payload.get("home_tips") or []
        home_tips = [
            sanitize_llm_plain_text(str(t), max_length=200)
            for t in tips_raw[:3]
            if sanitize_llm_plain_text(str(t), max_length=200)
        ]

        return ParentAnswerOut(
            answer=answer,
            home_tips=home_tips,
            pack_id=evidence.pack_id,
            concept_id=evidence.concept_id,
            concept_slug=evidence.concept_slug,
            mastery_topic=evidence.mastery_topic,
            source_count=evidence.source_count,
            grounded=_has_certified_parent_evidence(evidence),
            fallback=False,
            evidence_reason=_parent_evidence_reason(
                focus_areas=focus_areas, evidence=evidence
            ),
            evidence_summary=_parent_evidence_summary(evidence),
            model=result.model,
        )
