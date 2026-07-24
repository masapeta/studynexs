"""
StudyNexs Platform — FastAPI Dependencies
JWT validation, RBAC enforcement, DB/Redis injection, user cache.
"""

from __future__ import annotations

import json
from typing import Annotated

import redis.asyncio as redis
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import JWTError, decode_token
from app.core.tenant import validate_tenant_school_match

settings = get_settings()
logger = structlog.get_logger()

# ── Security scheme ──────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


# ── Redis connection ─────────────────────────────────────────────────────────

_redis_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Lazy-init async Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


# ── Current User model ───────────────────────────────────────────────────────


class CurrentUser(BaseModel):
    """Lightweight user object extracted from JWT + cache/DB."""

    id: str
    school_id: str
    role: str
    tenant_slug: str
    full_name: str
    mobile: str
    is_active: bool
    jti: str
    sid: str = ""  # refresh-session id (present on tokens issued after the sid-in-access change)


# ── Token blacklist check ────────────────────────────────────────────────────


async def _is_token_blacklisted(jti: str, r: redis.Redis) -> bool:
    """Check if a token's JTI is in the Redis blacklist."""
    return await r.exists(f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{jti}") > 0


# ── User cache (Redis 60s TTL) ───────────────────────────────────────────────


async def _get_cached_user(user_id: str, r: redis.Redis) -> dict | None:
    """Get user data from Redis cache."""
    data = await r.get(f"{settings.REDIS_USER_CACHE_PREFIX}{user_id}")
    if data:
        return json.loads(data)
    return None


async def _set_cached_user(user_id: str, user_data: dict, r: redis.Redis) -> None:
    """Cache user data in Redis with TTL."""
    await r.setex(
        f"{settings.REDIS_USER_CACHE_PREFIX}{user_id}",
        settings.REDIS_USER_CACHE_TTL,
        json.dumps(user_data),
    )


# ── Core dependency: get_current_user ────────────────────────────────────────


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
) -> CurrentUser:
    """
    Extract and validate the current user from the Bearer token.
    Uses Redis cache (60s TTL) to avoid a DB round-trip on every request.
    Falls back to DB on cache miss. Never blocks on Redis failure.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    jti = payload.get("jti", "")
    user_id = payload.get("sub", "")

    # Check blacklist. Redis is best-effort here (same degradation as the user cache below):
    # an outage must not 500 every authenticated request — the docstring promises exactly
    # this tolerance. Access tokens are ≤15 min, so honoring a revoked-but-unexpired token
    # during an outage is a bounded, logged degradation rather than a full auth outage.
    try:
        blacklisted = await _is_token_blacklisted(jti, r)
    except Exception:
        logger.warning("blacklist_check_degraded", reason="redis_unavailable")
        blacklisted = False
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Try Redis cache first
    try:
        cached = await _get_cached_user(user_id, r)
    except Exception:
        cached = None  # Redis down — fall through to DB

    if cached:
        if not cached.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated",
            )
        await validate_tenant_school_match(request, db, cached["school_id"])
        user = CurrentUser(
            id=user_id,
            school_id=cached["school_id"],
            role=cached["role"],
            tenant_slug=payload.get("tenant_slug", ""),
            full_name=cached["full_name"],
            mobile=cached["mobile"],
            is_active=cached["is_active"],
            jti=jti,
            sid=payload.get("sid", ""),
        )
        request.state.current_user = user
        return user

    # Cache miss — query DB
    from app.db.models.user import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated",
        )

    user_data = {
        "school_id": str(user.school_id),
        "role": user.role.value,
        "full_name": user.full_name,
        "mobile": user.mobile,
        "is_active": user.is_active,
    }

    # Cache for next request — don't fail if Redis is down
    try:
        await _set_cached_user(user_id, user_data, r)
    except Exception:
        pass

    await validate_tenant_school_match(request, db, str(user.school_id))

    current = CurrentUser(
        id=user_id,
        school_id=str(user.school_id),
        role=user.role.value,
        tenant_slug=payload.get("tenant_slug", ""),
        full_name=user.full_name,
        mobile=user.mobile,
        is_active=user.is_active,
        jti=jti,
        sid=payload.get("sid", ""),
    )
    request.state.current_user = current
    return current


# ── RBAC: require_roles ─────────────────────────────────────────────────────


def require_roles(*allowed_roles: str):
    """
    Dependency factory: restricts access to users with one of the allowed roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles("admin", "super_admin"))])
    """

    async def _check_role(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}",
            )
        return current_user

    return _check_role


# ── Rate Limiting Helper ─────────────────────────────────────────────────────


# INCR + first-hit EXPIRE atomically — a crash between the two can't leave the key
# without a TTL, which would otherwise lock the user out permanently.
_RATE_LIMIT_LUA = """
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return c
"""


async def check_rate_limit(
    key: str,
    max_attempts: int,
    window_seconds: int,
    r: redis.Redis,
) -> None:
    """Redis fixed-window rate limiter (atomic). Raises 429 if the limit is exceeded."""
    if settings.ENVIRONMENT == "testing":
        return

    redis_key = f"{settings.REDIS_RATE_LIMIT_PREFIX}{key}"
    try:
        current = int(await r.eval(_RATE_LIMIT_LUA, 1, redis_key, window_seconds))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        ) from None
    if current > max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(window_seconds)},
        )
