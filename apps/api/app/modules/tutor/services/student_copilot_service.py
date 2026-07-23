"""Student Copilot — grounded study assistance (Batch 25).

Uses weak-concept graph edges, approved ConceptCards, and hybrid RAG retrieval.
LLM output is supportive draft guidance — not authoritative grades or report cards.
"""
from __future__ import annotations

import json
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.gateway import LLMMessage, generate_llm, record_usage
from app.modules.ai.gateway.input_guard import sanitize_prompt_text
from app.modules.ai.gateway.output_guard import sanitize_llm_plain_text
from app.modules.ai.rag import HybridRetrievalOptions, HybridRetrievalService, RagService
from app.modules.ai.rag.service import RagService as RagSvc
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits
from app.modules.ai.services.assessment_grounding import resolve_citations
from app.modules.ai.vectorstore.base import VectorStore
from app.modules.curriculum.services.concept_card_service import ConceptCardService
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)
from app.modules.tutor.schemas.copilot import (
    CopilotAnswerOut,
    CopilotAskIn,
    StudyContextOut,
    WeakConceptStudyOut,
)

logger = structlog.get_logger()


def _build_ask_messages(
    *,
    board: str,
    grade: str,
    question: str,
    concept_title: str | None,
    card_explanation: str | None,
    context_text: str,
    source_count: int,
) -> list[LLMMessage]:
    concept_line = f"Focus concept: {concept_title}.\n" if concept_title else ""
    card_block = ""
    if card_explanation:
        card_block = f"\nAPPROVED CONCEPT CARD:\n{card_explanation}\n"
    system = (
        f"You are a supportive {board} tutor for a Class {grade} student in India. "
        "Answer ONLY using the CURRICULUM CONTEXT and concept card below. "
        "Be encouraging, clear, and age-appropriate. This is study help — not grading. "
        "Return JSON only."
    )
    user = (
        f"CURRICULUM CONTEXT (sources 1..{source_count} — cite by number):\n"
        f"{context_text or '(no curriculum context indexed yet)'}\n"
        f"{card_block}"
        f"{concept_line}"
        f"Student question:\n{question}\n\n"
        "Return JSON:\n"
        '{"answer": str, "citations": [int], "follow_up_hints": [str]}\n'
        "Keep answer under 120 words. Include 1-3 follow_up_hints."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


class StudentCopilotService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.weak = StudentWeakConceptService(db)
        self.cards = ConceptCardService(db)

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

    async def get_study_context(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> StudyContextOut:
        student = await self._student(school_id=school_id, student_id=student_id)
        if student is None:
            raise ValueError("Student not found")

        pairs = await self.weak.get_weak_concepts_for_student(
            school_id=school_id, student_id=student_id
        )
        weak_out: list[WeakConceptStudyOut] = []
        seen: set[uuid.UUID] = set()
        for concept, meta in pairs:
            if concept.id in seen:
                continue
            seen.add(concept.id)
            card = (
                await self.db.execute(
                    select(ConceptCard).where(
                        ConceptCard.school_id == school_id,
                        ConceptCard.concept_id == concept.id,
                        ConceptCard.status == ConceptCardStatus.APPROVED,
                    )
                )
            ).scalar_one_or_none()
            mastery = None
            if meta and meta.get("mastery_pct") is not None:
                mastery = float(meta["mastery_pct"])
            weak_out.append(
                WeakConceptStudyOut(
                    concept_id=concept.id,
                    slug=concept.slug,
                    title=concept.title,
                    pack_id=concept.pack_id,
                    mastery_pct=mastery,
                    has_approved_card=card is not None,
                )
            )

        if not weak_out:
            return StudyContextOut(
                student_id=student_id,
                weak_concepts=[],
                grounded=False,
            )

        primary = weak_out[0]
        rag = RagService(self.db, embedder=embedder, store=store)
        hybrid = HybridRetrievalService(self.db, rag)
        query = primary.title
        chunks = await hybrid.retrieve_hybrid(
            query,
            school_id=school_id,
            pack_id=primary.pack_id,
            top_k=5,
            options=HybridRetrievalOptions(
                concept_ids=[primary.concept_id],
                student_id=student_id,
                rerank=True,
            ),
        )
        context_text = RagSvc.build_context(chunks) if chunks else ""
        return StudyContextOut(
            student_id=student_id,
            weak_concepts=weak_out,
            primary_concept_slug=primary.slug,
            curriculum_context=context_text,
            source_count=len(chunks),
            grounded=bool(chunks),
        )

    async def ask(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        body: CopilotAskIn,
        user_id: uuid.UUID,
        role: str,
        embedder: EmbeddingService | None = None,
        store: VectorStore | None = None,
        credits_charged: int | None = None,
    ) -> CopilotAnswerOut:
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

        concept_slug = (body.concept_slug or "").strip() or None
        pack_id: uuid.UUID | None = None
        concept_id: uuid.UUID | None = None
        concept_title: str | None = None
        card_explanation: str | None = None

        if concept_slug:
            pairs = await self.weak.get_weak_concepts_for_student(
                school_id=school_id, student_id=student_id
            )
            for concept, _meta in pairs:
                if concept.slug == concept_slug:
                    pack_id = concept.pack_id
                    concept_id = concept.id
                    concept_title = concept.title
                    break
            match = await self.cards.get_approved_by_slug(
                school_id=school_id, slug=concept_slug, pack_id=pack_id
            )
            if match:
                card, concept = match
                pack_id = concept.pack_id
                concept_id = concept.id
                concept_title = concept.title
                card_explanation = card.explanation
        else:
            ctx = await self.get_study_context(
                school_id=school_id,
                student_id=student_id,
                embedder=embedder,
                store=store,
            )
            if ctx.primary_concept_slug and ctx.weak_concepts:
                primary = ctx.weak_concepts[0]
                pack_id = primary.pack_id
                concept_id = primary.concept_id
                concept_title = primary.title
                concept_slug = primary.slug
                match = await self.cards.get_approved_by_slug(
                    school_id=school_id, slug=concept_slug, pack_id=pack_id
                )
                if match:
                    card_explanation = match[0].explanation

        if pack_id is None:
            raise ValueError(
                "No weak concept or curriculum context found. "
                "Complete an assessment first or specify a concept."
            )

        rag = RagService(self.db, embedder=embedder, store=store)
        hybrid = HybridRetrievalService(self.db, rag)
        chunks = await hybrid.retrieve_hybrid(
            question,
            school_id=school_id,
            pack_id=pack_id,
            top_k=6,
            options=HybridRetrievalOptions(
                concept_ids=[concept_id] if concept_id else None,
                student_id=student_id,
                rerank=True,
            ),
        )
        context_text = RagSvc.build_context(chunks)
        sources = [
            {"index": i, "chapter": c.chapter, "topic": c.topic, "ref_id": c.ref_id}
            for i, c in enumerate(chunks, start=1)
        ]

        from app.db.models.academic import Class

        cls = (
            await self.db.execute(
                select(Class).where(
                    Class.id == student.class_id,
                    Class.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        school = (
            await self.db.execute(select(School).where(School.id == school_id))
        ).scalar_one()
        grade = cls.grade if cls else "10"
        board = school.board or "SSC"

        messages = _build_ask_messages(
            board=board,
            grade=grade,
            question=question,
            concept_title=concept_title,
            card_explanation=card_explanation,
            context_text=context_text,
            source_count=len(chunks),
        )

        purpose_tag = "tutor_explain"
        cost = credits_charged if credits_charged is not None else credits_for_purpose(purpose_tag)
        reserved = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=user_id,
                role=role,
                purpose_tag=purpose_tag,
                feature="student_copilot",
                credits=cost,
                ref_type="student_copilot",
            )

        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=800,
            temperature=0.35,
            feature="student_copilot",
            caller="ask_grounded",
        )

        await record_usage(
            self.db,
            feature="student_copilot",
            result=result,
            reserved_row=reserved,
            ref_type="student_copilot",
            ref_id=student_id,
        )

        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise ValueError("Copilot returned invalid JSON") from exc

        answer = sanitize_llm_plain_text(str(payload.get("answer", "")), max_length=1200)
        if not answer:
            raise ValueError("Copilot returned an empty answer")

        raw_citations = payload.get("citations") or []
        citations: list[int] = []
        for c in raw_citations:
            try:
                n = int(c)
                if 1 <= n <= len(sources):
                    citations.append(n)
            except (TypeError, ValueError):
                continue

        hints_raw = payload.get("follow_up_hints") or []
        follow_up_hints = [
            sanitize_llm_plain_text(str(h), max_length=200)
            for h in hints_raw[:3]
            if sanitize_llm_plain_text(str(h), max_length=200)
        ]

        if citations:
            resolve_citations(sources, citations)

        logger.info(
            "student_copilot_answer",
            student_id=str(student_id),
            concept_slug=concept_slug,
            grounded=bool(chunks),
        )

        return CopilotAnswerOut(
            answer=answer,
            concept_slug=concept_slug,
            concept_title=concept_title,
            pack_id=pack_id,
            concept_id=concept_id,
            source_count=len(chunks),
            citations=citations,
            follow_up_hints=follow_up_hints,
            grounded=bool(chunks or card_explanation),
            model=result.model,
        )
