"""
Cookie utility — HttpOnly refresh token cookie helpers.
"""
from __future__ import annotations

from fastapi import Response

from app.core.config import get_settings

settings = get_settings()


def set_refresh_cookie(response: Response, token: str) -> None:
    """Set the HttpOnly refresh token cookie."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        domain=settings.COOKIE_DOMAIN,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie on logout."""
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
