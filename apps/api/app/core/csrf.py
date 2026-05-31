"""
CSRF / origin checks for cookie-based auth endpoints.
"""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

from app.core.config import Environment, get_settings

settings = get_settings()


def validate_refresh_origin(request: Request) -> None:
    """
    Require browser refresh calls to come from an allowed Origin or Referer.
    Skipped in testing so httpx clients without Origin still work.
    """
    if settings.ENVIRONMENT == Environment.TESTING:
        return

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    candidate = origin
    if not candidate and referer:
        candidate = f"{urlparse(referer).scheme}://{urlparse(referer).netloc}"

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin required for refresh",
        )

    if candidate.rstrip("/") not in {o.rstrip("/") for o in settings.ALLOWED_ORIGINS}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin not allowed",
        )
