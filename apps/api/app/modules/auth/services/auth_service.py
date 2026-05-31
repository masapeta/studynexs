"""
Auth service — OTP management, password verification, token lifecycle.
"""
from __future__ import annotations

import secrets
import string
import uuid
from datetime import timedelta

import redis.asyncio as redis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User

settings = get_settings()
logger = structlog.get_logger()


class AuthService:
    """Handles OTP, password login, and token operations."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    # ── OTP ──────────────────────────────────────────────────────

    def _otp_scope(self, school_id: uuid.UUID, mobile: str) -> str:
        return f"{school_id}:{mobile}"

    async def send_otp(self, mobile: str, school_id: uuid.UUID) -> str:
        """
        Generate and store OTP in Redis.
        In production, this would call MSG91 API.
        Returns OTP for development logging only.
        """
        # Check cooldown
        scope = self._otp_scope(school_id, mobile)
        cooldown_key = f"{settings.REDIS_OTP_PREFIX}cooldown:{scope}"
        if await self.redis.exists(cooldown_key):
            raise ValueError("OTP already sent. Please wait before requesting another.")

        # Generate OTP
        otp = "".join(secrets.choice(string.digits) for _ in range(settings.OTP_LENGTH))

        # Store in Redis with expiry
        otp_key = f"{settings.REDIS_OTP_PREFIX}{scope}"
        await self.redis.setex(otp_key, settings.OTP_EXPIRE_MINUTES * 60, otp)

        # Store attempt counter
        attempts_key = f"{settings.REDIS_OTP_PREFIX}attempts:{scope}"
        await self.redis.setex(attempts_key, settings.OTP_EXPIRE_MINUTES * 60, "0")

        # Set cooldown
        await self.redis.setex(cooldown_key, settings.OTP_COOLDOWN_SECONDS, "1")

        # In production: call MSG91 API here
        # For development: log the OTP
        if settings.is_development:
            logger.info("OTP generated (dev mode)", mobile=mobile, otp=otp)

        return otp

    async def verify_otp(self, mobile: str, otp: str, school_id: uuid.UUID) -> User | None:
        """
        Verify OTP against Redis. Returns User if valid, None if OTP mismatch.
        Raises ValueError on max attempts exceeded.
        """
        scope = self._otp_scope(school_id, mobile)
        otp_key = f"{settings.REDIS_OTP_PREFIX}{scope}"
        attempts_key = f"{settings.REDIS_OTP_PREFIX}attempts:{scope}"

        # Check attempts
        attempts = await self.redis.get(attempts_key)
        if attempts and int(attempts) >= settings.OTP_MAX_ATTEMPTS:
            await self.redis.delete(otp_key, attempts_key)
            raise ValueError("Maximum OTP attempts exceeded. Please request a new OTP.")

        # Get stored OTP
        stored_otp = await self.redis.get(otp_key)
        if not stored_otp:
            raise ValueError("OTP expired or not found. Please request a new OTP.")

        # Increment attempts
        await self.redis.incr(attempts_key)

        if stored_otp != otp:
            return None

        # OTP valid — clean up
        await self.redis.delete(otp_key, attempts_key)

        # Find user
        result = await self.db.execute(
            select(User).where(User.mobile == mobile, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    # ── Password Login ───────────────────────────────────────────

    async def verify_password_login(
        self, username: str, password: str, school_id: uuid.UUID
    ) -> User | None:
        """
        Verify username/password. Returns User if valid.
        Identical error signatures to prevent enumeration.
        """
        result = await self.db.execute(
            select(User).where(
                User.username == username,
                User.school_id == school_id,
                User.is_active == True,
            )
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    # ── Token Operations ─────────────────────────────────────────

    async def issue_tokens(self, user: User) -> tuple[str, str]:
        """
        Issue access + refresh tokens for a user.
        Returns (access_token, refresh_token).
        """
        from app.db.models.school import School

        slug_result = await self.db.execute(
            select(School.tenant_slug).where(School.id == user.school_id)
        )
        tenant_slug = slug_result.scalar_one_or_none() or ""

        access_token = create_access_token(
            user_id=str(user.id),
            school_id=str(user.school_id),
            role=user.role.value,
            tenant_slug=tenant_slug,
        )
        refresh_token, jti = create_refresh_token(
            user_id=str(user.id),
            school_id=str(user.school_id),
        )
        await self._store_refresh_jti(str(user.id), jti)
        return access_token, refresh_token

    async def _store_refresh_jti(self, user_id: str, jti: str) -> None:
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await self.redis.setex(f"{settings.REDIS_REFRESH_JTI_PREFIX}{user_id}", ttl, jti)

    async def rotate_refresh_session(
        self, user: User, presented_jti: str
    ) -> tuple[str, str]:
        """
        Atomic refresh rotation with per-user lock and reuse detection.
        """
        lock_key = f"{settings.REDIS_REFRESH_LOCK_PREFIX}{user.id}"
        acquired = await self.redis.set(lock_key, "1", nx=True, ex=15)
        if not acquired:
            raise ValueError("Refresh already in progress")

        try:
            stored = await self.redis.get(f"{settings.REDIS_REFRESH_JTI_PREFIX}{user.id}")
            stored_jti = stored.decode() if isinstance(stored, bytes) else stored
            if stored_jti and stored_jti != presented_jti:
                await self.blacklist_token(
                    presented_jti, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
                )
                await self.redis.delete(f"{settings.REDIS_REFRESH_JTI_PREFIX}{user.id}")
                raise ValueError("Refresh token reuse detected")

            await self.blacklist_token(
                presented_jti, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
            )
            return await self.issue_tokens(user)
        finally:
            await self.redis.delete(lock_key)

    async def blacklist_token(self, jti: str, ttl_seconds: int) -> None:
        """Add a token JTI to the Redis blacklist."""
        await self.redis.setex(
            f"{settings.REDIS_TOKEN_BLACKLIST_PREFIX}{jti}",
            ttl_seconds,
            "1",
        )

    async def invalidate_user_cache(self, user_id: str) -> None:
        """Clear user cache on role/status change."""
        await self.redis.delete(f"{settings.REDIS_USER_CACHE_PREFIX}{user_id}")
