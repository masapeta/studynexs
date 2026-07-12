"""ConceptCard service — draft → approve workflow for tutor grounding."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import PackStatus
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.curriculum.schemas.concept_card import ConceptCardCreate, ConceptCardUpdate
from app.modules.curriculum.services.pack_service import PackError, PackService


class ConceptCardError(ValueError):
    """Concept card cannot be created or modified."""


class ConceptCardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.packs = PackService(db)

    async def _get_concept(
        self, *, school_id: uuid.UUID, concept_id: uuid.UUID
    ) -> CurriculumConcept:
        concept = (
            await self.db.execute(
                select(CurriculumConcept).where(
                    CurriculumConcept.id == concept_id,
                    CurriculumConcept.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if concept is None:
            raise ConceptCardError("Concept not found")
        return concept

    async def _require_pack_approved(self, *, school_id: uuid.UUID, pack_id: uuid.UUID) -> None:
        pack = await self.packs.get_pack(school_id, pack_id)
        if pack.status != PackStatus.APPROVED:
            raise ConceptCardError("Concept cards require an approved curriculum pack")

    async def create_card(
        self,
        *,
        school_id: uuid.UUID,
        concept_id: uuid.UUID,
        data: ConceptCardCreate,
        created_by: uuid.UUID,
    ) -> ConceptCard:
        concept = await self._get_concept(school_id=school_id, concept_id=concept_id)
        await self._require_pack_approved(school_id=school_id, pack_id=concept.pack_id)

        existing = (
            await self.db.execute(
                select(ConceptCard).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id == concept_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConceptCardError("A concept card already exists for this concept")

        card = ConceptCard(
            school_id=school_id,
            pack_id=concept.pack_id,
            concept_id=concept_id,
            title=data.title.strip(),
            explanation=data.explanation.strip(),
            examples=data.examples,
            hints=data.hints,
            visual_kind=data.visual_kind or "generic",
            status=ConceptCardStatus.DRAFT,
            created_by=created_by,
        )
        self.db.add(card)
        await self.db.flush()
        return card

    async def get_card(
        self, *, school_id: uuid.UUID, card_id: uuid.UUID
    ) -> ConceptCard:
        card = (
            await self.db.execute(
                select(ConceptCard).where(
                    ConceptCard.id == card_id, ConceptCard.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if card is None:
            raise ConceptCardError("Concept card not found")
        return card

    async def list_by_pack(
        self, *, school_id: uuid.UUID, pack_id: uuid.UUID
    ) -> list[ConceptCard]:
        await self.packs.get_pack(school_id, pack_id)
        result = await self.db.execute(
            select(ConceptCard)
            .where(ConceptCard.school_id == school_id, ConceptCard.pack_id == pack_id)
            .order_by(ConceptCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_card(
        self,
        *,
        school_id: uuid.UUID,
        card_id: uuid.UUID,
        data: ConceptCardUpdate,
    ) -> ConceptCard:
        card = await self.get_card(school_id=school_id, card_id=card_id)
        if card.status != ConceptCardStatus.DRAFT:
            raise ConceptCardError("Approved concept cards are immutable")

        if data.title is not None:
            card.title = data.title.strip()
        if data.explanation is not None:
            card.explanation = data.explanation.strip()
        if data.examples is not None:
            card.examples = data.examples
        if data.hints is not None:
            card.hints = data.hints
        if data.visual_kind is not None:
            card.visual_kind = data.visual_kind
        await self.db.flush()
        return card

    async def approve_card(
        self,
        *,
        school_id: uuid.UUID,
        card_id: uuid.UUID,
        approved_by: uuid.UUID,
    ) -> ConceptCard:
        card = await self.get_card(school_id=school_id, card_id=card_id)
        if card.status == ConceptCardStatus.APPROVED:
            raise ConceptCardError("Concept card is already approved")
        card.status = ConceptCardStatus.APPROVED
        card.approved_by = approved_by
        card.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        return card

    async def get_approved_by_slug(
        self, *, school_id: uuid.UUID, slug: str
    ) -> tuple[ConceptCard, CurriculumConcept] | None:
        """Lookup approved card by concept slug (tutor retrieval)."""
        row = (
            await self.db.execute(
                select(ConceptCard, CurriculumConcept)
                .join(
                    CurriculumConcept,
                    CurriculumConcept.id == ConceptCard.concept_id,
                )
                .where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.status == ConceptCardStatus.APPROVED,
                    CurriculumConcept.slug == slug,
                )
                .limit(1)
            )
        ).first()
        if row is None:
            return None
        return row[0], row[1]
