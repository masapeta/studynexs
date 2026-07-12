"""ConceptCard API — teacher draft → approve for tutor grounding (Batch 18)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.curriculum.schemas.concept_card import (
    ConceptCardCreate,
    ConceptCardOut,
    ConceptCardUpdate,
)
from app.modules.curriculum.services.concept_card_service import (
    ConceptCardError,
    ConceptCardService,
)
from app.modules.curriculum.services.pack_service import PackError
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_BUILD = ("teacher", "class_incharge", "admin", "super_admin")
_READ = ("teacher", "class_incharge", "admin", "super_admin")


def _err(e: ConceptCardError) -> HTTPException:
    msg = str(e)
    code = (
        404
        if "not found" in msg.lower()
        else 409
        if "already" in msg.lower() or "immutable" in msg.lower()
        else 400
    )
    return HTTPException(status_code=code, detail=msg)


async def _out(svc: ConceptCardService, card) -> ConceptCardOut:
    concept = (
        await svc.db.execute(
            select(CurriculumConcept).where(CurriculumConcept.id == card.concept_id)
        )
    ).scalar_one_or_none()
    data = ConceptCardOut.model_validate(card)
    if concept:
        data.concept_slug = concept.slug
        data.concept_title = concept.title
    return data


@router.post(
    "/concepts/{concept_id}/cards",
    response_model=APIResponse[ConceptCardOut],
    status_code=201,
)
async def create_concept_card(
    concept_id: uuid.UUID,
    body: ConceptCardCreate,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = ConceptCardService(db)
    try:
        card = await svc.create_card(
            school_id=uuid.UUID(current_user.school_id),
            concept_id=concept_id,
            data=body,
            created_by=uuid.UUID(current_user.id),
        )
    except ConceptCardError as e:
        raise _err(e)
    return APIResponse(
        data=await _out(svc, card),
        message="Concept card created (draft)",
    )


@router.get(
    "/packs/{pack_id}/concept-cards",
    response_model=APIResponse[list[ConceptCardOut]],
)
async def list_pack_concept_cards(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = ConceptCardService(db)
    try:
        cards = await svc.list_by_pack(
            school_id=uuid.UUID(current_user.school_id), pack_id=pack_id
        )
    except PackError as e:
        raise HTTPException(status_code=404, detail=str(e))
    out = [await _out(svc, c) for c in cards]
    return APIResponse(data=out)


@router.get(
    "/concept-cards/{card_id}",
    response_model=APIResponse[ConceptCardOut],
)
async def get_concept_card(
    card_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = ConceptCardService(db)
    try:
        card = await svc.get_card(
            school_id=uuid.UUID(current_user.school_id), card_id=card_id
        )
    except ConceptCardError as e:
        raise _err(e)
    return APIResponse(data=await _out(svc, card))


@router.put(
    "/concept-cards/{card_id}",
    response_model=APIResponse[ConceptCardOut],
)
async def update_concept_card(
    card_id: uuid.UUID,
    body: ConceptCardUpdate,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = ConceptCardService(db)
    try:
        card = await svc.update_card(
            school_id=uuid.UUID(current_user.school_id),
            card_id=card_id,
            data=body,
        )
    except ConceptCardError as e:
        raise _err(e)
    return APIResponse(data=await _out(svc, card), message="Concept card updated")


@router.post(
    "/concept-cards/{card_id}/approve",
    response_model=APIResponse[ConceptCardOut],
)
async def approve_concept_card(
    card_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = ConceptCardService(db)
    try:
        card = await svc.approve_card(
            school_id=uuid.UUID(current_user.school_id),
            card_id=card_id,
            approved_by=uuid.UUID(current_user.id),
        )
    except ConceptCardError as e:
        raise _err(e)
    return APIResponse(
        data=await _out(svc, card),
        message="Concept card approved — available for tutor grounding",
    )
