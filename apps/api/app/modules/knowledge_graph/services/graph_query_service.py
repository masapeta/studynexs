"""Graph query helpers for copilots and dashboards (Batch 23)."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge, KgEdgeType, KgNodeType
from app.modules.curriculum.services.pack_service import PackService
from app.modules.knowledge_graph.schemas.graph import ConceptContextOut, ConceptOut
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)


class GraphQueryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.packs = PackService(db)
        self.weak = StudentWeakConceptService(db)

    async def get_concept_context(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        concept_id: uuid.UUID,
    ) -> ConceptContextOut:
        await self.packs.get_pack(school_id, pack_id)
        concept = (
            await self.db.execute(
                select(CurriculumConcept).where(
                    CurriculumConcept.id == concept_id,
                    CurriculumConcept.school_id == school_id,
                    CurriculumConcept.pack_id == pack_id,
                )
            )
        ).scalar_one_or_none()
        if concept is None:
            raise ValueError("Concept not found in this pack")

        card = (
            await self.db.execute(
                select(ConceptCard).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id == concept_id,
                )
            )
        ).scalar_one_or_none()

        question_count = (
            await self.db.scalar(
                select(func.count())
                .select_from(KgEdge)
                .where(
                    KgEdge.school_id == school_id,
                    KgEdge.edge_type == KgEdgeType.TESTS,
                    KgEdge.to_node_type == KgNodeType.CONCEPT,
                    KgEdge.to_id == concept_id,
                )
            )
        ) or 0

        weak_count = (
            await self.db.scalar(
                select(func.count())
                .select_from(KgEdge)
                .where(
                    KgEdge.school_id == school_id,
                    KgEdge.pack_id == pack_id,
                    KgEdge.edge_type == KgEdgeType.STRUGGLES_WITH,
                    KgEdge.to_node_type == KgNodeType.CONCEPT,
                    KgEdge.to_id == concept_id,
                )
            )
        ) or 0

        return ConceptContextOut(
            concept=ConceptOut.model_validate(concept),
            has_approved_card=card is not None and card.status == ConceptCardStatus.APPROVED,
            concept_card_status=card.status.value if card else None,
            linked_question_count=int(question_count),
            weak_student_count=int(weak_count),
        )

    async def list_student_weak_concepts(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_id: uuid.UUID | None = None,
        pack_id: uuid.UUID | None = None,
    ) -> list[ConceptOut]:
        pairs = await self.weak.get_weak_concepts_for_student(
            school_id=school_id,
            student_id=student_id,
            subject_id=subject_id,
            pack_id=pack_id,
        )
        seen: set[uuid.UUID] = set()
        out: list[ConceptOut] = []
        for concept, _meta in pairs:
            if concept.id in seen:
                continue
            seen.add(concept.id)
            out.append(ConceptOut.model_validate(concept))
        return out
