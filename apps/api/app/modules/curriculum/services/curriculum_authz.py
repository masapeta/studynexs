"""Curriculum pack draft-edit and approval authorization."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.staff_permissions import StaffScope, get_staff_scope
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumTopic,
)


def assert_curriculum_draft_edit(
    scope: StaffScope, class_id: uuid.UUID, subject_id: uuid.UUID
) -> None:
    """Admin, class incharge, or mapped subject teacher may edit drafts for class×subject."""
    if not scope.can_edit_curriculum_draft(class_id, subject_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Curriculum draft editing requires admin, class incharge, "
                "or a subject assignment for this class and subject"
            ),
        )


def assert_curriculum_approve(scope: StaffScope, pack: CurriculumPack) -> None:
    """Class incharge or admin may approve; authors cannot approve their own pack."""
    if not scope.can_approve_curriculum_pack(pack):
        if (
            not scope.is_admin
            and pack.class_id in scope.incharge_class_ids
            and pack.created_by == scope.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You cannot approve a curriculum pack you authored — "
                    "principal or admin approval is required"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Curriculum approval requires admin or class incharge for this class",
        )


def assert_curriculum_manage(scope: StaffScope, class_id: uuid.UUID) -> None:
    """Legacy incharge/admin gate — prefer assert_curriculum_draft_edit for mutations."""
    if scope.is_admin:
        return
    if class_id in scope.incharge_class_ids:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Curriculum onboarding requires admin or class incharge for this class",
    )


async def _get_pack(
    db: AsyncSession, *, school_id: uuid.UUID, pack_id: uuid.UUID
) -> CurriculumPack:
    pack = await db.scalar(
        select(CurriculumPack).where(
            CurriculumPack.id == pack_id,
            CurriculumPack.school_id == school_id,
        )
    )
    if pack is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum pack not found",
        )
    return pack


async def _class_id_for_pack(
    db: AsyncSession, *, school_id: uuid.UUID, pack_id: uuid.UUID
) -> uuid.UUID:
    return (await _get_pack(db, school_id=school_id, pack_id=pack_id)).class_id


async def _pack_for_chapter(
    db: AsyncSession, *, school_id: uuid.UUID, chapter_id: uuid.UUID
) -> CurriculumPack:
    pack = await db.scalar(
        select(CurriculumPack)
        .join(CurriculumChapter, CurriculumChapter.pack_id == CurriculumPack.id)
        .where(
            CurriculumChapter.id == chapter_id,
            CurriculumChapter.school_id == school_id,
            CurriculumPack.school_id == school_id,
        )
    )
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return pack


async def _pack_for_topic(
    db: AsyncSession, *, school_id: uuid.UUID, topic_id: uuid.UUID
) -> CurriculumPack:
    pack = await db.scalar(
        select(CurriculumPack)
        .join(CurriculumChapter, CurriculumChapter.pack_id == CurriculumPack.id)
        .join(CurriculumTopic, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .where(
            CurriculumTopic.id == topic_id,
            CurriculumTopic.school_id == school_id,
            CurriculumChapter.school_id == school_id,
            CurriculumPack.school_id == school_id,
        )
    )
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return pack


async def _pack_for_outcome(
    db: AsyncSession, *, school_id: uuid.UUID, outcome_id: uuid.UUID
) -> CurriculumPack:
    outcome = (
        await db.execute(
            select(CurriculumLearningOutcome).where(
                CurriculumLearningOutcome.id == outcome_id,
                CurriculumLearningOutcome.school_id == school_id,
            )
        )
    ).scalar_one_or_none()
    if outcome is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Learning outcome not found"
        )
    if outcome.topic_id:
        return await _pack_for_topic(db, school_id=school_id, topic_id=outcome.topic_id)
    if outcome.chapter_id:
        return await _pack_for_chapter(db, school_id=school_id, chapter_id=outcome.chapter_id)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Learning outcome not found"
    )


async def assert_curriculum_draft_edit_pack(
    db: AsyncSession, current_user: CurrentUser, pack_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    pack = await _get_pack(db, school_id=school_id, pack_id=pack_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_draft_edit(scope, pack.class_id, pack.subject_id)


async def assert_curriculum_approve_pack(
    db: AsyncSession, current_user: CurrentUser, pack_id: uuid.UUID
) -> CurriculumPack:
    school_id = uuid.UUID(current_user.school_id)
    pack = await _get_pack(db, school_id=school_id, pack_id=pack_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_approve(scope, pack)
    return pack


async def assert_curriculum_manage_pack(
    db: AsyncSession, current_user: CurrentUser, pack_id: uuid.UUID
) -> None:
    await assert_curriculum_draft_edit_pack(db, current_user, pack_id)


async def assert_curriculum_manage_chapter(
    db: AsyncSession, current_user: CurrentUser, chapter_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    pack = await _pack_for_chapter(db, school_id=school_id, chapter_id=chapter_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_draft_edit(scope, pack.class_id, pack.subject_id)


async def assert_curriculum_manage_topic(
    db: AsyncSession, current_user: CurrentUser, topic_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    pack = await _pack_for_topic(db, school_id=school_id, topic_id=topic_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_draft_edit(scope, pack.class_id, pack.subject_id)


async def assert_curriculum_manage_outcome(
    db: AsyncSession, current_user: CurrentUser, outcome_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    pack = await _pack_for_outcome(db, school_id=school_id, outcome_id=outcome_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_draft_edit(scope, pack.class_id, pack.subject_id)
