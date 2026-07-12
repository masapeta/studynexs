"""Content Review Queue service — gap-filling HITL for tutor content (Batch 20)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.content_review import (
    ContentReviewItem,
    ContentReviewItemType,
    ContentReviewSource,
    ContentReviewStatus,
)
from app.db.models.document_ingestion import DocumentIngestion
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.curriculum.schemas.concept_card import ConceptCardCreate, ConceptCardUpdate
from app.modules.curriculum.schemas.content_review import EnqueueConceptGapRequest
from app.modules.curriculum.services.concept_card_service import (
    ConceptCardError,
    ConceptCardService,
)
from app.modules.curriculum.services.pack_service import PackError, PackService

logger = structlog.get_logger()

_GAP_PLACEHOLDER_EXPLANATION = (
    "A tutor Concept Card is needed for this concept. "
    "Replace this draft with a clear, student-friendly explanation before approving."
)


class ContentReviewError(ValueError):
    """Queue item cannot be created or reviewed."""


class ContentReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.packs = PackService(db)
        self.cards = ConceptCardService(db)

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
            raise ContentReviewError("Concept not found")
        return concept

    async def _pending_concept_gap(
        self, *, school_id: uuid.UUID, concept_id: uuid.UUID
    ) -> ContentReviewItem | None:
        return (
            await self.db.execute(
                select(ContentReviewItem).where(
                    ContentReviewItem.school_id == school_id,
                    ContentReviewItem.concept_id == concept_id,
                    ContentReviewItem.item_type == ContentReviewItemType.CONCEPT_CARD_GAP,
                    ContentReviewItem.status == ContentReviewStatus.PENDING,
                )
            )
        ).scalar_one_or_none()

    async def _has_approved_card(
        self, *, school_id: uuid.UUID, concept_id: uuid.UUID
    ) -> bool:
        row = (
            await self.db.execute(
                select(ConceptCard.id).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id == concept_id,
                    ConceptCard.status == ConceptCardStatus.APPROVED,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    def _default_gap_payload(self, concept: CurriculumConcept) -> dict:
        return {
            "title": f"Teach: {concept.title}",
            "explanation": _GAP_PLACEHOLDER_EXPLANATION,
            "examples": [],
            "hints": [],
            "visual_kind": "generic",
        }

    async def enqueue_concept_gap(
        self,
        *,
        school_id: uuid.UUID,
        concept_id: uuid.UUID,
        created_by: uuid.UUID,
        source: ContentReviewSource,
        data: EnqueueConceptGapRequest | None = None,
    ) -> ContentReviewItem | None:
        """Idempotent: skip when approved card exists or pending gap already queued."""
        concept = await self._get_concept(school_id=school_id, concept_id=concept_id)
        await self.packs.get_pack(school_id, concept.pack_id)

        if await self._has_approved_card(school_id=school_id, concept_id=concept_id):
            return None

        existing = await self._pending_concept_gap(
            school_id=school_id, concept_id=concept_id
        )
        if existing is not None:
            return existing

        payload = self._default_gap_payload(concept)
        if data is not None:
            if data.title:
                payload["title"] = data.title.strip()
            if data.explanation:
                payload["explanation"] = data.explanation.strip()
            if data.examples is not None:
                payload["examples"] = data.examples
            if data.hints is not None:
                payload["hints"] = data.hints

        item = ContentReviewItem(
            school_id=school_id,
            pack_id=concept.pack_id,
            item_type=ContentReviewItemType.CONCEPT_CARD_GAP,
            status=ContentReviewStatus.PENDING,
            source=source,
            concept_id=concept_id,
            title=f"Concept card needed: {concept.title}",
            draft_payload=payload,
            created_by=created_by,
        )
        self.db.add(item)
        await self.db.flush()
        logger.info(
            "content_review_enqueued",
            item_type="concept_card_gap",
            concept_id=str(concept_id),
            source=source.value,
        )
        return item

    async def enqueue_concept_gap_by_slug(
        self,
        *,
        school_id: uuid.UUID,
        slug: str,
        created_by: uuid.UUID,
        source: ContentReviewSource = ContentReviewSource.TUTOR_GAP,
    ) -> ContentReviewItem | None:
        concept = (
            await self.db.execute(
                select(CurriculumConcept).where(
                    CurriculumConcept.school_id == school_id,
                    CurriculumConcept.slug == slug,
                )
            )
        ).scalar_one_or_none()
        if concept is None:
            return None
        return await self.enqueue_concept_gap(
            school_id=school_id,
            concept_id=concept.id,
            created_by=created_by,
            source=source,
        )

    async def enqueue_document_ingest(
        self,
        *,
        school_id: uuid.UUID,
        ingestion: DocumentIngestion,
    ) -> ContentReviewItem | None:
        """Queue ingested document for teacher review before broader copilot/tutor use."""
        existing = (
            await self.db.execute(
                select(ContentReviewItem).where(
                    ContentReviewItem.school_id == school_id,
                    ContentReviewItem.item_type == ContentReviewItemType.DOCUMENT_INGEST,
                    ContentReviewItem.source_ref_id == ingestion.id,
                    ContentReviewItem.status == ContentReviewStatus.PENDING,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        item = ContentReviewItem(
            school_id=school_id,
            pack_id=ingestion.pack_id,
            item_type=ContentReviewItemType.DOCUMENT_INGEST,
            status=ContentReviewStatus.PENDING,
            source=ContentReviewSource.DOCUMENT_INGEST,
            source_ref_id=ingestion.id,
            title=f"Review document: {ingestion.source_name}",
            draft_payload={
                "ingestion_id": str(ingestion.id),
                "file_id": str(ingestion.file_id),
                "source_name": ingestion.source_name,
                "doc_type": ingestion.doc_type.value,
                "chunks_indexed": ingestion.chunks_indexed,
                "version": ingestion.version,
            },
            created_by=ingestion.ingested_by,
        )
        self.db.add(item)
        await self.db.flush()
        logger.info(
            "content_review_enqueued",
            item_type="document_ingest",
            ingestion_id=str(ingestion.id),
        )
        return item

    async def get_item(
        self, *, school_id: uuid.UUID, item_id: uuid.UUID
    ) -> ContentReviewItem:
        item = (
            await self.db.execute(
                select(ContentReviewItem).where(
                    ContentReviewItem.id == item_id,
                    ContentReviewItem.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if item is None:
            raise ContentReviewError("Review item not found")
        return item

    async def list_queue(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID | None = None,
        status: ContentReviewStatus | None = ContentReviewStatus.PENDING,
        item_type: ContentReviewItemType | None = None,
        limit: int = 50,
    ) -> tuple[list[ContentReviewItem], int]:
        filters = [ContentReviewItem.school_id == school_id]
        if pack_id is not None:
            filters.append(ContentReviewItem.pack_id == pack_id)
        if status is not None:
            filters.append(ContentReviewItem.status == status)
        if item_type is not None:
            filters.append(ContentReviewItem.item_type == item_type)

        pending_count = (
            await self.db.scalar(
                select(func.count())
                .select_from(ContentReviewItem)
                .where(
                    ContentReviewItem.school_id == school_id,
                    ContentReviewItem.status == ContentReviewStatus.PENDING,
                    *([ContentReviewItem.pack_id == pack_id] if pack_id else []),
                )
            )
        ) or 0

        rows = await self.db.execute(
            select(ContentReviewItem)
            .where(*filters)
            .order_by(ContentReviewItem.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all()), int(pending_count)

    async def update_item(
        self,
        *,
        school_id: uuid.UUID,
        item_id: uuid.UUID,
        title: str | None = None,
        draft_payload: dict | None = None,
    ) -> ContentReviewItem:
        item = await self.get_item(school_id=school_id, item_id=item_id)
        if item.status != ContentReviewStatus.PENDING:
            raise ContentReviewError("Only pending items can be edited")
        if item.item_type != ContentReviewItemType.CONCEPT_CARD_GAP:
            raise ContentReviewError("Only concept card gap items support draft edits")

        if title is not None:
            item.title = title.strip()
        if draft_payload is not None:
            item.draft_payload = draft_payload
        await self.db.flush()
        return item

    async def _promote_concept_card(
        self,
        *,
        school_id: uuid.UUID,
        concept_id: uuid.UUID,
        payload: dict,
        reviewed_by: uuid.UUID,
    ) -> ConceptCard:
        if await self._has_approved_card(school_id=school_id, concept_id=concept_id):
            raise ContentReviewError("An approved concept card already exists")

        create_data = ConceptCardCreate(
            title=str(payload.get("title") or "Concept card"),
            explanation=str(payload.get("explanation") or ""),
            examples=payload.get("examples"),
            hints=payload.get("hints"),
            visual_kind=str(payload.get("visual_kind") or "generic"),
        )

        existing_card = (
            await self.db.execute(
                select(ConceptCard).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id == concept_id,
                )
            )
        ).scalar_one_or_none()

        if existing_card is None:
            card = await self.cards.create_card(
                school_id=school_id,
                concept_id=concept_id,
                data=create_data,
                created_by=reviewed_by,
            )
        else:
            if existing_card.status == ConceptCardStatus.APPROVED:
                raise ContentReviewError("An approved concept card already exists")
            card = await self.cards.update_card(
                school_id=school_id,
                card_id=existing_card.id,
                data=ConceptCardUpdate(
                    title=create_data.title,
                    explanation=create_data.explanation,
                    examples=create_data.examples,
                    hints=create_data.hints,
                    visual_kind=create_data.visual_kind,
                ),
            )

        return await self.cards.approve_card(
            school_id=school_id, card_id=card.id, approved_by=reviewed_by
        )

    async def approve_item(
        self,
        *,
        school_id: uuid.UUID,
        item_id: uuid.UUID,
        reviewed_by: uuid.UUID,
    ) -> ContentReviewItem:
        item = await self.get_item(school_id=school_id, item_id=item_id)
        if item.status != ContentReviewStatus.PENDING:
            raise ContentReviewError("Item is not pending review")

        now = datetime.now(timezone.utc)
        if item.item_type == ContentReviewItemType.CONCEPT_CARD_GAP:
            if item.concept_id is None:
                raise ContentReviewError("Concept card gap item missing concept")
            card = await self._promote_concept_card(
                school_id=school_id,
                concept_id=item.concept_id,
                payload=item.draft_payload,
                reviewed_by=reviewed_by,
            )
            item.result_card_id = card.id

        item.status = ContentReviewStatus.APPROVED
        item.reviewed_by = reviewed_by
        item.reviewed_at = now
        await self.db.flush()
        logger.info(
            "content_review_approved",
            item_id=str(item_id),
            item_type=item.item_type.value,
        )
        return item

    async def reject_item(
        self,
        *,
        school_id: uuid.UUID,
        item_id: uuid.UUID,
        reviewed_by: uuid.UUID,
        reason: str,
    ) -> ContentReviewItem:
        item = await self.get_item(school_id=school_id, item_id=item_id)
        if item.status != ContentReviewStatus.PENDING:
            raise ContentReviewError("Item is not pending review")

        item.status = ContentReviewStatus.REJECTED
        item.reviewed_by = reviewed_by
        item.reviewed_at = datetime.now(timezone.utc)
        item.rejection_reason = reason.strip()
        await self.db.flush()
        return item
