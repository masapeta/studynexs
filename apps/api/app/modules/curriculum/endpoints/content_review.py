"""Content Review Queue API (Batch 20)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.db.models.content_review import ContentReviewItemType, ContentReviewSource, ContentReviewStatus
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.curriculum.schemas.content_review import (
    ContentReviewItemOut,
    ContentReviewQueueOut,
    ContentReviewUpdate,
    EnqueueConceptGapRequest,
    RejectContentReviewRequest,
)
from app.modules.curriculum.services.content_review_service import (
    ContentReviewError,
    ContentReviewService,
)
from app.modules.curriculum.services.concept_card_service import ConceptCardError
from app.modules.curriculum.services.pack_service import PackError
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_READ = ("teacher", "class_incharge", "admin", "super_admin")
_REVIEW = ("teacher", "class_incharge", "admin", "super_admin")


def _err(e: ContentReviewError) -> HTTPException:
    msg = str(e)
    code = 404 if "not found" in msg.lower() else 409 if "already" in msg.lower() else 400
    return HTTPException(status_code=code, detail=msg)


async def _out(svc: ContentReviewService, item) -> ContentReviewItemOut:
    data = ContentReviewItemOut.model_validate(item)
    if item.concept_id:
        concept = (
            await svc.db.execute(
                select(CurriculumConcept).where(CurriculumConcept.id == item.concept_id)
            )
        ).scalar_one_or_none()
        if concept:
            data.concept_slug = concept.slug
            data.concept_title = concept.title
    return data


@router.get("/content-review/queue", response_model=APIResponse[ContentReviewQueueOut])
async def list_content_review_queue(
    pack_id: uuid.UUID | None = None,
    status: ContentReviewStatus | None = Query(default=ContentReviewStatus.PENDING),
    item_type: ContentReviewItemType | None = None,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = ContentReviewService(db)
    school_id = uuid.UUID(current_user.school_id)
    if pack_id is not None:
        try:
            await svc.packs.get_pack(school_id, pack_id)
        except PackError as e:
            raise HTTPException(status_code=404, detail=str(e))

    items, pending_count = await svc.list_queue(
        school_id=school_id,
        pack_id=pack_id,
        status=status,
        item_type=item_type,
    )
    out = [await _out(svc, item) for item in items]
    return APIResponse(
        data=ContentReviewQueueOut(items=out, pending_count=pending_count)
    )


@router.get(
    "/content-review/items/{item_id}",
    response_model=APIResponse[ContentReviewItemOut],
)
async def get_content_review_item(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = ContentReviewService(db)
    try:
        item = await svc.get_item(
            school_id=uuid.UUID(current_user.school_id), item_id=item_id
        )
    except ContentReviewError as e:
        raise _err(e)
    return APIResponse(data=await _out(svc, item))


@router.post(
    "/concepts/{concept_id}/content-review",
    response_model=APIResponse[ContentReviewItemOut],
    status_code=201,
)
async def enqueue_concept_content_review(
    concept_id: uuid.UUID,
    body: EnqueueConceptGapRequest | None = None,
    current_user: CurrentUser = Depends(require_roles(*_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    svc = ContentReviewService(db)
    try:
        item = await svc.enqueue_concept_gap(
            school_id=uuid.UUID(current_user.school_id),
            concept_id=concept_id,
            created_by=uuid.UUID(current_user.id),
            source=ContentReviewSource.TEACHER,
            data=body,
        )
    except ContentReviewError as e:
        raise _err(e)
    if item is None:
        raise HTTPException(
            status_code=409,
            detail="Approved concept card already exists — no review needed",
        )
    return APIResponse(
        data=await _out(svc, item),
        message="Concept card gap queued for review",
    )


@router.put(
    "/content-review/items/{item_id}",
    response_model=APIResponse[ContentReviewItemOut],
)
async def update_content_review_item(
    item_id: uuid.UUID,
    body: ContentReviewUpdate,
    current_user: CurrentUser = Depends(require_roles(*_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    svc = ContentReviewService(db)
    try:
        item = await svc.update_item(
            school_id=uuid.UUID(current_user.school_id),
            item_id=item_id,
            title=body.title,
            draft_payload=body.draft_payload,
        )
    except ContentReviewError as e:
        raise _err(e)
    return APIResponse(data=await _out(svc, item), message="Review draft updated")


@router.post(
    "/content-review/items/{item_id}/approve",
    response_model=APIResponse[ContentReviewItemOut],
)
async def approve_content_review_item(
    item_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    svc = ContentReviewService(db)
    try:
        item = await svc.approve_item(
            school_id=uuid.UUID(current_user.school_id),
            item_id=item_id,
            reviewed_by=uuid.UUID(current_user.id),
        )
    except ContentReviewError as e:
        raise _err(e)
    except ConceptCardError as e:
        raise _err(ContentReviewError(str(e)))
    return APIResponse(
        data=await _out(svc, item),
        message="Content approved — available for tutor grounding where applicable",
    )


@router.post(
    "/content-review/items/{item_id}/reject",
    response_model=APIResponse[ContentReviewItemOut],
)
async def reject_content_review_item(
    item_id: uuid.UUID,
    body: RejectContentReviewRequest,
    current_user: CurrentUser = Depends(require_roles(*_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    svc = ContentReviewService(db)
    try:
        item = await svc.reject_item(
            school_id=uuid.UUID(current_user.school_id),
            item_id=item_id,
            reviewed_by=uuid.UUID(current_user.id),
            reason=body.reason,
        )
    except ContentReviewError as e:
        raise _err(e)
    return APIResponse(data=await _out(svc, item), message="Review item rejected")
