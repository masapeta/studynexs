"""Curriculum pack API — HOD builds a draft syllabus, then approves to immutable."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_roles
from app.core.staff_permissions import get_staff_scope
from app.modules.curriculum.schemas.grounding import CurriculumGroundingOut
from app.modules.curriculum.schemas.pack import (
    ChapterIn,
    ChapterOut,
    ChapterUpdate,
    LearningOutcomeIn,
    LearningOutcomeOut,
    LearningOutcomeUpdate,
    PackAuditEventOut,
    PackCreate,
    PackDetailOut,
    PackOut,
    PackUpdate,
    TopicIn,
    TopicOut,
    TopicUpdate,
)
from app.modules.curriculum.services.curriculum_authz import (
    assert_curriculum_approve_pack,
    assert_curriculum_draft_edit,
    assert_curriculum_manage_chapter,
    assert_curriculum_manage_outcome,
    assert_curriculum_manage_pack,
    assert_curriculum_manage_topic,
)
from app.modules.curriculum.services.curriculum_grounding import ground_approved_pack
from app.modules.curriculum.services.pack_detail import build_pack_detail
from app.modules.curriculum.services.pack_service import PackError, PackService
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_DRAFT_EDIT = ("teacher", "class_incharge", "admin", "super_admin")
_APPROVE = ("class_incharge", "admin", "super_admin")
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


async def _assert_draft_edit(
    db: AsyncSession, current_user: CurrentUser, class_id: uuid.UUID, subject_id: uuid.UUID
) -> None:
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_draft_edit(scope, class_id, subject_id)


async def _detail(svc: PackService, pack) -> PackDetailOut:
    return await build_pack_detail(svc, pack)


@router.post("/packs", response_model=APIResponse[PackOut], status_code=201)
async def create_pack(
    body: PackCreate,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await _assert_draft_edit(db, current_user, body.class_id, body.subject_id)
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
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_pack(db, current_user, pack_id)
    svc = PackService(db)
    try:
        pack = await svc.update_pack(
            uuid.UUID(current_user.school_id),
            pack_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(data=PackOut.model_validate(pack), message="Pack updated")


@router.post("/packs/{pack_id}/chapters", response_model=APIResponse[ChapterOut], status_code=201)
async def add_chapter(
    pack_id: uuid.UUID,
    body: ChapterIn,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_pack(db, current_user, pack_id)
    svc = PackService(db)
    try:
        chapter = await svc.add_chapter(
            uuid.UUID(current_user.school_id),
            pack_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    topics = (await svc.get_topics_for_chapters([chapter.id])).get(chapter.id, [])
    topic_ids = [t.id for t in topics]
    outcomes_by_topic = await svc.get_outcomes_for_topics(topic_ids)
    outcomes_by_chapter = await svc.get_outcomes_for_chapters([chapter.id])
    return APIResponse(
        data=ChapterOut(
            id=chapter.id,
            number=chapter.number,
            title=chapter.title,
            order_index=chapter.order_index,
            learning_outcomes=[
                LearningOutcomeOut.model_validate(lo)
                for lo in outcomes_by_chapter.get(chapter.id, [])
            ],
            topics=[
                TopicOut(
                    id=t.id,
                    title=t.title,
                    order_index=t.order_index,
                    concepts=t.concepts,
                    learning_outcomes=[
                        LearningOutcomeOut.model_validate(lo)
                        for lo in outcomes_by_topic.get(t.id, [])
                    ],
                )
                for t in topics
            ],
        ),
        message="Chapter added",
    )


@router.put("/chapters/{chapter_id}", response_model=APIResponse[ChapterOut])
async def update_chapter(
    chapter_id: uuid.UUID,
    body: ChapterUpdate,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_chapter(db, current_user, chapter_id)
    svc = PackService(db)
    try:
        chapter = await svc.update_chapter(
            uuid.UUID(current_user.school_id),
            chapter_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    topics = (await svc.get_topics_for_chapters([chapter.id])).get(chapter.id, [])
    topic_ids = [t.id for t in topics]
    outcomes_by_topic = await svc.get_outcomes_for_topics(topic_ids)
    outcomes_by_chapter = await svc.get_outcomes_for_chapters([chapter.id])
    return APIResponse(
        data=ChapterOut(
            id=chapter.id,
            number=chapter.number,
            title=chapter.title,
            order_index=chapter.order_index,
            learning_outcomes=[
                LearningOutcomeOut.model_validate(lo)
                for lo in outcomes_by_chapter.get(chapter.id, [])
            ],
            topics=[
                TopicOut(
                    id=t.id,
                    title=t.title,
                    order_index=t.order_index,
                    concepts=t.concepts,
                    learning_outcomes=[
                        LearningOutcomeOut.model_validate(lo)
                        for lo in outcomes_by_topic.get(t.id, [])
                    ],
                )
                for t in topics
            ],
        ),
        message="Chapter updated",
    )


@router.delete("/chapters/{chapter_id}", response_model=APIResponse[None])
async def delete_chapter(
    chapter_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_chapter(db, current_user, chapter_id)
    svc = PackService(db)
    try:
        await svc.delete_chapter(
            uuid.UUID(current_user.school_id),
            chapter_id,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(data=None, message="Chapter removed")


@router.post("/chapters/{chapter_id}/topics", response_model=APIResponse[TopicOut], status_code=201)
async def add_topic(
    chapter_id: uuid.UUID,
    body: TopicIn,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_chapter(db, current_user, chapter_id)
    svc = PackService(db)
    try:
        topic = await svc.add_topic(
            uuid.UUID(current_user.school_id),
            chapter_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    outcomes = await svc.get_outcomes_for_topics([topic.id])
    return APIResponse(
        data=TopicOut(
            id=topic.id,
            title=topic.title,
            order_index=topic.order_index,
            concepts=topic.concepts,
            learning_outcomes=[
                LearningOutcomeOut.model_validate(lo) for lo in outcomes.get(topic.id, [])
            ],
        ),
        message="Topic added",
    )


@router.put("/topics/{topic_id}", response_model=APIResponse[TopicOut])
async def update_topic(
    topic_id: uuid.UUID,
    body: TopicUpdate,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_topic(db, current_user, topic_id)
    svc = PackService(db)
    try:
        topic = await svc.update_topic(
            uuid.UUID(current_user.school_id),
            topic_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    outcomes = await svc.get_outcomes_for_topics([topic.id])
    return APIResponse(
        data=TopicOut(
            id=topic.id,
            title=topic.title,
            order_index=topic.order_index,
            concepts=topic.concepts,
            learning_outcomes=[
                LearningOutcomeOut.model_validate(lo) for lo in outcomes.get(topic.id, [])
            ],
        ),
        message="Topic updated",
    )


@router.post(
    "/topics/{topic_id}/learning-outcomes",
    response_model=APIResponse[LearningOutcomeOut],
    status_code=201,
)
async def add_topic_learning_outcome(
    topic_id: uuid.UUID,
    body: LearningOutcomeIn,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_topic(db, current_user, topic_id)
    svc = PackService(db)
    try:
        outcome = await svc.add_learning_outcome_to_topic(
            uuid.UUID(current_user.school_id),
            topic_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(
        data=LearningOutcomeOut.model_validate(outcome),
        message="Learning outcome added to topic",
    )


@router.post(
    "/chapters/{chapter_id}/learning-outcomes",
    response_model=APIResponse[LearningOutcomeOut],
    status_code=201,
)
async def add_chapter_learning_outcome(
    chapter_id: uuid.UUID,
    body: LearningOutcomeIn,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_chapter(db, current_user, chapter_id)
    svc = PackService(db)
    try:
        outcome = await svc.add_learning_outcome_to_chapter(
            uuid.UUID(current_user.school_id),
            chapter_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(
        data=LearningOutcomeOut.model_validate(outcome),
        message="Learning outcome added to chapter",
    )


@router.put(
    "/learning-outcomes/{outcome_id}",
    response_model=APIResponse[LearningOutcomeOut],
)
async def update_learning_outcome(
    outcome_id: uuid.UUID,
    body: LearningOutcomeUpdate,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_outcome(db, current_user, outcome_id)
    svc = PackService(db)
    try:
        outcome = await svc.update_learning_outcome(
            uuid.UUID(current_user.school_id),
            outcome_id,
            body,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(
        data=LearningOutcomeOut.model_validate(outcome),
        message="Learning outcome updated",
    )


@router.delete("/learning-outcomes/{outcome_id}", response_model=APIResponse[None])
async def delete_learning_outcome(
    outcome_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_DRAFT_EDIT)),
    db: AsyncSession = Depends(get_db),
):
    await assert_curriculum_manage_outcome(db, current_user, outcome_id)
    svc = PackService(db)
    try:
        await svc.delete_learning_outcome(
            uuid.UUID(current_user.school_id),
            outcome_id,
            actor_id=uuid.UUID(current_user.id),
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(data=None, message="Learning outcome removed")


@router.get("/packs/{pack_id}/grounding", response_model=APIResponse[CurriculumGroundingOut])
async def preview_pack_grounding(
    pack_id: uuid.UUID,
    topics: list[str] | None = Query(default=None),
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Preview RAG retrieval from an approved pack (shared Curriculum Intelligence facade)."""
    try:
        grounding = await ground_approved_pack(
            db,
            school_id=uuid.UUID(current_user.school_id),
            pack_id=pack_id,
            topics=topics,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(
        data=CurriculumGroundingOut(
            pack_id=grounding.pack_id,
            pack_status=grounding.pack_status,
            pack_version=grounding.pack_version,
            source_count=grounding.chunk_count,
            sources=grounding.sources,
            context_preview=grounding.context_text[:500],
        )
    )


@router.get("/packs/{pack_id}/audit", response_model=APIResponse[list[PackAuditEventOut]])
async def list_pack_audit(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_READ)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    try:
        events = await svc.list_pack_audit(uuid.UUID(current_user.school_id), pack_id)
    except PackError as e:
        raise _err(e)
    return APIResponse(
        data=[PackAuditEventOut.model_validate(e) for e in events],
    )


@router.post("/packs/{pack_id}/approve", response_model=APIResponse[PackOut])
async def approve_pack(
    pack_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(*_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    svc = PackService(db)
    await assert_curriculum_approve_pack(db, current_user, pack_id)
    try:
        pack = await svc.approve_pack(
            uuid.UUID(current_user.school_id), pack_id, uuid.UUID(current_user.id)
        )
    except PackError as e:
        raise _err(e)
    return APIResponse(
        data=PackOut.model_validate(pack), message="Curriculum pack approved — now immutable"
    )
