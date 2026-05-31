"""AI module endpoints.

Phase-1 Teacher-AI routes (question-paper generation, AI-assisted grading, student
summaries) will be added here. For now this exposes a status endpoint confirming the
module is mounted and which providers are configured (admins only — no keys leaked).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, require_roles

settings = get_settings()
router = APIRouter()


@router.get("/health")
async def ai_health(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
) -> dict:
    """AI module status + which providers have API keys configured (booleans only)."""
    return {
        "status": "ok",
        "module": "ai",
        "default_provider": settings.AI_DEFAULT_PROVIDER,
        "providers_configured": {
            "gemini": bool(settings.GEMINI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY),
        },
    }
