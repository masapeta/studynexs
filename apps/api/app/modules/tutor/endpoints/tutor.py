"""Tutor endpoints — Mistake Recovery lessons for students (and parents viewing child)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.modules.tutor.schemas.tutor import TutorLessonOut, TutorRecommendationOut
from app.modules.tutor.services.tutor_service import get_lesson, list_recommendations
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.get(
    "/students/{student_id}/recommendations",
    response_model=APIResponse[list[TutorRecommendationOut]],
)
async def tutor_recommendations(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Topics to revisit — from exam mistakes and weak mastery."""
    await assert_can_access_student(current_user, db, student_id)
    recs = await list_recommendations(
        db, school_id=uuid.UUID(current_user.school_id), student_id=student_id
    )
    return APIResponse(data=recs)


@router.get(
    "/students/{student_id}/lessons/{lesson_key}",
    response_model=APIResponse[TutorLessonOut],
)
async def tutor_lesson(
    student_id: uuid.UUID,
    lesson_key: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Teacher-style lesson with narration + visual steps (voice/image on client)."""
    await assert_can_access_student(current_user, db, student_id)
    lesson = await get_lesson(
        db,
        school_id=uuid.UUID(current_user.school_id),
        student_id=student_id,
        lesson_key=lesson_key,
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return APIResponse(data=lesson)
