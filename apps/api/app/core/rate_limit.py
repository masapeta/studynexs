"""
API rate limiting — Redis sliding window, per user/school on authenticated routes.
"""
from __future__ import annotations

import redis.asyncio as redis
from fastapi import Depends, Request

from app.core.config import Environment, get_settings
from app.core.dependencies import CurrentUser, check_rate_limit, get_current_user, get_redis

settings = get_settings()


async def enforce_api_rate_limit(
    *,
    key: str,
    max_requests: int,
    window_seconds: int,
    r: redis.Redis,
) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    if settings.ENVIRONMENT == Environment.TESTING:
        return
    await check_rate_limit(key, max_requests, window_seconds, r)


def rate_limit(
    action: str,
    *,
    max_requests: int | None = None,
    window_seconds: int | None = None,
):
    """
    Dependency factory — keys by school_id + user_id on authenticated routes.
    """
    limit = max_requests or settings.API_RATE_LIMIT_READ_PER_MIN
    window = window_seconds or settings.API_RATE_LIMIT_WINDOW_SECONDS

    async def _dependency(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
        r: redis.Redis = Depends(get_redis),
    ) -> None:
        redis_key = f"api:{action}:{current_user.school_id}:{current_user.id}"
        await enforce_api_rate_limit(
            key=redis_key,
            max_requests=limit,
            window_seconds=window,
            r=r,
        )

    return Depends(_dependency)
