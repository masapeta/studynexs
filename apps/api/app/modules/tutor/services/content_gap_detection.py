"""Background content-gap detection (Q7, plan Rev 2 §6).

Student GETs are strictly read-only. Instead, after the learner ledger changes (results
release / withdrawal), this background handler looks at the learner weak-concept edges of the
affected class × subject and queues one concept-card gap per concept that has no approved
card. Creation is idempotent (``uq_content_review_pending_gap`` + ON CONFLICT DO NOTHING) and
audited once per created item.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditLog
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.content_review import (
    ContentReviewItem,
    ContentReviewItemType,
    ContentReviewSource,
    ContentReviewStatus,
)
from app.db.models.knowledge_graph import (
    KG_AUDIENCE_LEARNER,
    CurriculumConcept,
    KgEdge,
    KgEdgeType,
    KgNodeType,
)
from app.db.models.student import Student

logger = structlog.get_logger()

_GAP_EXPLANATION = (
    "A tutor Concept Card is needed for this concept. "
    "Replace this draft with a clear, student-friendly explanation before approving."
)


async def detect_learner_content_gaps(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> int:
    """Queue gaps for learner weak concepts lacking an approved card. Returns items created."""
    if actor_id is None:
        return 0
    student_ids = select(Student.id).where(
        Student.school_id == school_id, Student.class_id == class_id
    )
    concept_ids = set(
        (
            await db.execute(
                select(KgEdge.to_id).where(
                    KgEdge.school_id == school_id,
                    KgEdge.edge_type == KgEdgeType.STRUGGLES_WITH,
                    KgEdge.audience == KG_AUDIENCE_LEARNER,
                    KgEdge.from_node_type == KgNodeType.STUDENT,
                    KgEdge.from_id.in_(student_ids),
                    KgEdge.to_node_type == KgNodeType.CONCEPT,
                    KgEdge.metadata_["subject_id"].astext == str(subject_id),
                )
            )
        ).scalars().all()
    )
    if not concept_ids:
        return 0
    with_card = set(
        (
            await db.execute(
                select(ConceptCard.concept_id).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id.in_(concept_ids),
                    ConceptCard.status == ConceptCardStatus.APPROVED,
                )
            )
        ).scalars().all()
    )
    missing = concept_ids - with_card
    if not missing:
        return 0
    concepts = (
        await db.execute(
            select(CurriculumConcept).where(
                CurriculumConcept.school_id == school_id,
                CurriculumConcept.id.in_(missing),
            )
        )
    ).scalars().all()
    created = 0
    for concept in concepts:
        item_id = await db.scalar(
            pg_insert(ContentReviewItem)
            .values(
                id=uuid.uuid4(),
                school_id=school_id,
                pack_id=concept.pack_id,
                item_type=ContentReviewItemType.CONCEPT_CARD_GAP,
                status=ContentReviewStatus.PENDING,
                source=ContentReviewSource.TUTOR_GAP,
                concept_id=concept.id,
                title=f"Concept card needed: {concept.title}",
                draft_payload={
                    "title": f"Teach: {concept.title}",
                    "explanation": _GAP_EXPLANATION,
                    "examples": [],
                    "hints": [],
                    "visual_kind": "generic",
                },
                created_by=actor_id,
            )
            .on_conflict_do_nothing(
                index_elements=["school_id", "concept_id"],
                index_where=(
                    (ContentReviewItem.item_type == ContentReviewItemType.CONCEPT_CARD_GAP)
                    & (ContentReviewItem.status == ContentReviewStatus.PENDING)
                ),
            )
            .returning(ContentReviewItem.id)
        )
        if item_id is None:
            continue
        created += 1
        db.add(
            AuditLog(
                school_id=school_id,
                user_id=actor_id,
                action="content_review.gap_detected",
                resource_type="content_review_item",
                resource_id=str(item_id),
                details={
                    "concept_id": str(concept.id),
                    "source": "learner_ledger",
                    "class_id": str(class_id),
                    "subject_id": str(subject_id),
                },
            )
        )
    await db.flush()
    if created:
        logger.info(
            "learner_content_gaps_detected", school_id=str(school_id), created=created
        )
    return created
