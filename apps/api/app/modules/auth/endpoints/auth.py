"""
Auth API endpoints — OTP, password login, refresh, logout.
"""
from __future__ import annotations

import redis.asyncio as redis
import structlog
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import (
    CurrentUser,
    check_rate_limit,
    get_current_user,
    get_redis,
)
from app.core.security import decode_token
from app.core.csrf import validate_refresh_origin
from app.core.tenant import resolve_auth_school_id, validate_tenant_school_match
from app.modules.auth.cookie_util import clear_refresh_cookie, set_refresh_cookie
from app.modules.auth.schemas.auth import (
    MessageResponse,
    PasswordLoginRequest,
    RefreshResponse,
    SendOTPRequest,
    TokenResponse,
    VerifyOTPRequest,
)
from app.modules.auth.services.auth_service import AuthService

settings = get_settings()
logger = structlog.get_logger()
router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For from trusted proxies."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── POST /auth/send-otp ─────────────────────────────────────────────────────


@router.post("/send-otp", response_model=MessageResponse)
async def send_otp(
    body: SendOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """Send OTP to mobile number."""
    client_ip = _get_client_ip(request)
    await check_rate_limit(
        key=f"send_otp:{client_ip}",
        max_attempts=settings.AUTH_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        r=r,
    )

    school_id = await resolve_auth_school_id(request, db)
    service = AuthService(db, r)
    try:
        otp = await service.send_otp(body.mobile, school_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    msg = "OTP sent successfully"
    if settings.is_development:
        msg += f" (dev OTP: {otp})"

    return MessageResponse(message=msg)


# ── POST /auth/verify-otp ───────────────────────────────────────────────────


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    body: VerifyOTPRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """Verify OTP and issue tokens."""
    client_ip = _get_client_ip(request)
    await check_rate_limit(
        key=f"verify_otp:{client_ip}",
        max_attempts=settings.AUTH_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        r=r,
    )

    school_id = await resolve_auth_school_id(request, db)
    service = AuthService(db, r)
    try:
        user = await service.verify_otp(body.mobile, body.otp, school_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated",
        )

    await validate_tenant_school_match(request, db, str(user.school_id))
    access_token, refresh_token = await service.issue_tokens(user)
    set_refresh_cookie(response, refresh_token)

    logger.info("user_login_otp", user_id=str(user.id), mobile=body.mobile)

    return TokenResponse(
        access_token=access_token,
        role=user.role.value,
        user_id=str(user.id),
        school_id=str(user.school_id),
        full_name=user.full_name,
    )


# ── POST /auth/login (password) ─────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
async def login_password(
    body: PasswordLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """Login with username and password."""
    client_ip = _get_client_ip(request)

    # Rate limit by IP + username composite
    await check_rate_limit(
        key=f"login:{client_ip}:{body.username}",
        max_attempts=settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
        window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        r=r,
    )

    school_id = await resolve_auth_school_id(request, db)
    service = AuthService(db, r)
    user = await service.verify_password_login(body.username, body.password, school_id)

    if not user:
        # Identical error message — prevents username enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",  # Same message — no hint about deactivation
        )

    await validate_tenant_school_match(request, db, str(user.school_id))
    access_token, refresh_token = await service.issue_tokens(user)
    set_refresh_cookie(response, refresh_token)

    logger.info("user_login_password", user_id=str(user.id), username=body.username)

    return TokenResponse(
        access_token=access_token,
        role=user.role.value,
        user_id=str(user.id),
        school_id=str(user.school_id),
        full_name=user.full_name,
    )


# ── POST /auth/refresh ──────────────────────────────────────────────────────


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """Refresh access token using HttpOnly cookie."""
    validate_refresh_origin(request)
    cookie_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        payload = decode_token(cookie_token)
    except JWTError:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check blacklist
    jti = payload.get("jti", "")
    blacklist_key = f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{jti}"
    if await r.exists(blacklist_key):
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Load user from DB
    from app.db.models.user import User
    from sqlalchemy import select

    user_id = payload.get("sub", "")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    service = AuthService(db, r)
    await validate_tenant_school_match(request, db, str(user.school_id))
    try:
        access_token, new_refresh_token = await service.rotate_refresh_session(user, jti)
    except ValueError as e:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    set_refresh_cookie(response, new_refresh_token)

    return RefreshResponse(access_token=access_token)


# ── POST /auth/logout ───────────────────────────────────────────────────────


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    r: redis.Redis = Depends(get_redis),
):
    """Logout — blacklist access token + clear refresh cookie."""
    # Blacklist the access token
    await r.setex(
        f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{current_user.jti}",
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "1",
    )

    # Blacklist refresh cookie if present
    cookie_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if cookie_token:
        try:
            payload = decode_token(cookie_token)
            refresh_jti = payload.get("jti", "")
            if refresh_jti:
                await r.setex(
                    f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{refresh_jti}",
                    settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                    "1",
                )
        except JWTError:
            pass  # Already expired — ignore

    clear_refresh_cookie(response)
    logger.info("user_logout", user_id=current_user.id)

    return MessageResponse(message="Logged out successfully")
