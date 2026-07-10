"""Tutor endpoints — Mistake Recovery lessons for students (and parents viewing child)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.authorization import assert_can_access_student
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.core.rate_limit import rate_limit
from app.modules.ai.gateway.input_guard import (
    sanitize_lesson_key,
    sanitize_prompt_text,
    sanitize_tts_voice,
)
from app.modules.tutor.schemas.tutor import TutorLessonOut, TutorRecommendationOut
from app.modules.tutor.services.tts_service import (
    default_tts_voice,
    resolve_tts_backend,
    synthesize_speech,
    tts_enabled,
)
from app.modules.tutor.services.tutor_service import get_lesson, list_recommendations
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)

_TTS_RATE = {"max_requests": 40, "window_seconds": 60}
_TTS_ROLES = frozenset({"student", "parent", "teacher", "class_incharge", "admin", "super_admin"})


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1200)
    voice: str | None = Field(None, max_length=60)

    @field_validator("text", mode="before")
    @classmethod
    def _sanitize_text(cls, v: object) -> str:
        cleaned = sanitize_prompt_text(
            str(v), max_length=1200, field_name="text", reject_injection=True
        )
        if not cleaned:
            raise ValueError("text is required")
        return cleaned

    @field_validator("voice", mode="before")
    @classmethod
    def _sanitize_voice(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        return sanitize_tts_voice(str(v), default=default_tts_voice())


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
    try:
        safe_key = sanitize_lesson_key(lesson_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    lesson = await get_lesson(
        db,
        school_id=uuid.UUID(current_user.school_id),
        student_id=student_id,
        lesson_key=safe_key,
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return APIResponse(data=lesson)


@router.get("/tts/status")
async def tts_status(current_user: CurrentUser = Depends(get_current_user)):
    """Whether cloud Neural TTS is available — the client uses it, else Web Speech."""
    backend = resolve_tts_backend()
    return APIResponse(
        data={
            "enabled": backend != "off",
            "voice": default_tts_voice(),
            "backend": backend,
        }
    )


@router.post("/tts", dependencies=[rate_limit("tutor_tts", **_TTS_RATE)])
async def tutor_tts(
    body: TtsRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Synthesize a lesson step to MP3 (soft female Indian voice). 503 → client falls back."""
    if current_user.role not in _TTS_ROLES:
        raise HTTPException(
            status_code=403, detail="Voice synthesis is not available for this role"
        )
    if not tts_enabled():
        raise HTTPException(status_code=503, detail="Voice synthesis is not configured")
    try:
        audio = await synthesize_speech(body.text, body.voice)
    except Exception:
        raise HTTPException(status_code=502, detail="Voice synthesis failed")
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff"},
    )
