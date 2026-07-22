"""Curriculum onboarding / pack mutation authorization."""

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


def assert_curriculum_manage(scope: StaffScope, class_id: uuid.UUID) -> None:
    """Admin/principal or class incharge for the target class may onboard or approve."""
    if scope.is_admin:
        return
    if class_id in scope.incharge_class_ids:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Curriculum onboarding requires admin or class incharge for this class",
    )


async def _class_id_for_pack(
    db: AsyncSession, *, school_id: uuid.UUID, pack_id: uuid.UUID
) -> uuid.UUID:
    class_id = await db.scalar(
        select(CurriculumPack.class_id).where(
            CurriculumPack.id == pack_id,
            CurriculumPack.school_id == school_id,
        )
    )
    if class_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum pack not found",
        )
    return class_id


async def _class_id_for_chapter(
    db: AsyncSession, *, school_id: uuid.UUID, chapter_id: uuid.UUID
) -> uuid.UUID:
    class_id = await db.scalar(
        select(CurriculumPack.class_id)
        .join(CurriculumChapter, CurriculumChapter.pack_id == CurriculumPack.id)
        .where(
            CurriculumChapter.id == chapter_id,
            CurriculumChapter.school_id == school_id,
            CurriculumPack.school_id == school_id,
        )
    )
    if class_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return class_id


async def _class_id_for_topic(
    db: AsyncSession, *, school_id: uuid.UUID, topic_id: uuid.UUID
) -> uuid.UUID:
    class_id = await db.scalar(
        select(CurriculumPack.class_id)
        .join(CurriculumChapter, CurriculumChapter.pack_id == CurriculumPack.id)
        .join(CurriculumTopic, CurriculumTopic.chapter_id == CurriculumChapter.id)
        .where(
            CurriculumTopic.id == topic_id,
            CurriculumTopic.school_id == school_id,
            CurriculumChapter.school_id == school_id,
            CurriculumPack.school_id == school_id,
        )
    )
    if class_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return class_id


async def _class_id_for_outcome(
    db: AsyncSession, *, school_id: uuid.UUID, outcome_id: uuid.UUID
) -> uuid.UUID:
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
        return await _class_id_for_topic(db, school_id=school_id, topic_id=outcome.topic_id)
    if outcome.chapter_id:
        return await _class_id_for_chapter(db, school_id=school_id, chapter_id=outcome.chapter_id)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Learning outcome not found"
    )


async def assert_curriculum_manage_pack(
    db: AsyncSession, current_user: CurrentUser, pack_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    class_id = await _class_id_for_pack(db, school_id=school_id, pack_id=pack_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_manage(scope, class_id)


async def assert_curriculum_manage_chapter(
    db: AsyncSession, current_user: CurrentUser, chapter_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    class_id = await _class_id_for_chapter(db, school_id=school_id, chapter_id=chapter_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_manage(scope, class_id)


async def assert_curriculum_manage_topic(
    db: AsyncSession, current_user: CurrentUser, topic_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    class_id = await _class_id_for_topic(db, school_id=school_id, topic_id=topic_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_manage(scope, class_id)


async def assert_curriculum_manage_outcome(
    db: AsyncSession, current_user: CurrentUser, outcome_id: uuid.UUID
) -> None:
    school_id = uuid.UUID(current_user.school_id)
    class_id = await _class_id_for_outcome(db, school_id=school_id, outcome_id=outcome_id)
    scope = await get_staff_scope(db, current_user)
    assert_curriculum_manage(scope, class_id)
