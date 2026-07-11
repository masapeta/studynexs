"""Curriculum pack API — HOD builds a draft syllabus, then approves to immutable."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.modules.curriculum.schemas.pack import (
    ChapterIn,
    ChapterOut,
    PackCreate,
    PackDetailOut,
    PackOut,
    PackUpdate,
    TopicIn,
    TopicOut,
)
from app.modules.curriculum.services.pack_service import PackError, PackService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_BUILD = ("class_incharge", "admin", "super_admin")
_READ = ("teacher", "class_incharge", "admin", "super_admin")


def _err(e: PackError) -> HTTPException:
    msg = str(e)
    code = (
        404
        if "not found" in msg.lower()
        else 409
        if "immutable" in msg.lower() or "already" in msg.lower()
        else 400
    )
    return HTTPException(status_code=code, detail=msg)


async def _detail(svc: PackService, pack) -> PackDetailOut:
    chapters = await svc.get_chapters(pack.id)
    topics_by_ch = await svc.get_topics_for_chapters([c.id for c in chapters])
    out = PackDetailOut.model_validate(pack)
    out.chapters = [
        ChapterOut(
            id=c.id,
            number=c.number,
            title=c.title,
            order_index=c.order_index,
            topics=[TopicOut.model_validate(t) for t in topics_by_ch.get(c.id, [])],
        )
        for c in chapters
    ]
    return out


@router.post("/packs", response_model=APIResponse[PackOut], status_code=201)
async def create_pack(
    body: PackCreate,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        pack = await svc.create_pack(
            uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(data=PackOut.model_validate(pack), message="Curriculum pack created (draft)")


@router.get("/packs", response_model=APIResponse[list[PackOut]])
async def list_packs(
    class_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    packs = await svc.list_packs(
        uuid.UUID(current_user.school_id), class_id=class_id, subject_id=subject_id
    )
    return APIResponse(data=[PackOut.model_validate(p) for p in packs])


@router.get("/packs/{pack_id}", response_model=APIResponse[PackDetailOut])
async def get_pack(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        pack = await svc.get_pack(uuid.UUID(current_user.school_id), pack_id)
    except PackError as e:
        raise _err(e)
    return APIResponse(data=await _detail(svc, pack))


@router.put("/packs/{pack_id}", response_model=APIResponse[PackOut])
async def update_pack(
    pack_id: uuid.UUID,
    body: PackUpdate,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        pack = await svc.update_pack(uuid.UUID(current_user.school_id), pack_id, body)
    except PackError as e:
        raise _err(e)
    return APIResponse(data=PackOut.model_validate(pack), message="Pack updated")


@router.post("/packs/{pack_id}/chapters", response_model=APIResponse[ChapterOut], status_code=201)
async def add_chapter(
    pack_id: uuid.UUID,
    body: ChapterIn,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        chapter = await svc.add_chapter(uuid.UUID(current_user.school_id), pack_id, body)
    except PackError as e:
        raise _err(e)
    topics = (await svc.get_topics_for_chapters([chapter.id])).get(chapter.id, [])
    return APIResponse(
        data=ChapterOut(
            id=chapter.id,
            number=chapter.number,
            title=chapter.title,
            order_index=chapter.order_index,
            topics=[TopicOut.model_validate(t) for t in topics],
        ),
        message="Chapter added",
    )


@router.post("/chapters/{chapter_id}/topics", response_model=APIResponse[TopicOut], status_code=201)
async def add_topic(
    chapter_id: uuid.UUID,
    body: TopicIn,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        topic = await svc.add_topic(uuid.UUID(current_user.school_id), chapter_id, body)
    except PackError as e:
        raise _err(e)
    return APIResponse(data=TopicOut.model_validate(topic), message="Topic added")


@router.post("/packs/{pack_id}/approve", response_model=APIResponse[PackOut])
async def approve_pack(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_BUILD)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        pack = await svc.approve_pack(
            uuid.UUID(current_user.school_id), pack_id, uuid.UUID(current_user.id)
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(
        data=PackOut.model_validate(pack), message="Curriculum pack approved — now immutable"
    )
