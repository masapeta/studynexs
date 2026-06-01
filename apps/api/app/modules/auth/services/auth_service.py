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

    async def issue_tokens(self, user: User, sid: str | None = None) -> tuple[str, str]:
        """
        Issue access + refresh tokens for a user.

        A fresh ``sid`` (default) starts a new session — i.e. a login on a new device.
        Passing an existing ``sid`` rotates the token within that session (refresh).
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
        sid = sid or str(uuid.uuid4())
        refresh_token, jti = create_refresh_token(
            user_id=str(user.id),
            school_id=str(user.school_id),
            sid=sid,
        )
        await self._store_refresh_jti(str(user.id), sid, jti)
        return access_token, refresh_token

    def _refresh_key(self, user_id: str, sid: str) -> str:
        return f"{settings.REDIS_REFRESH_JTI_PREFIX}{user_id}:{sid}"

    async def _store_refresh_jti(self, user_id: str, sid: str, jti: str) -> None:
        # Value is "<current_jti>|<prev_jti>"; a fresh login has no predecessor.
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await self.redis.setex(self._refresh_key(user_id, sid), ttl, f"{jti}|")

    # Atomic compare-and-swap with a one-rotation grace. The session value is
    # "<current_jti>|<prev_jti>". Rotation is allowed if the presented jti is the current
    # jti OR the immediate predecessor — the predecessor case is the benign multi-tab race
    # (two tabs share the cookie, each fires a refresh with the same jti; one wins, the other
    # would otherwise look like reuse). Lock-free, so sessions on different devices (different
    # keys) never contend. Returns: 1 = rotated, 0 = unknown/logged-out session (key gone,
    # nothing to revoke), -1 = a jti older than the grace → genuine reuse, revoke the session.
    _ROTATE_LUA = """
    local v = redis.call('GET', KEYS[1])
    if v == false then return 0 end
    local cur, prev
    local sep = string.find(v, '|', 1, true)
    if sep == nil then
        cur = v
        prev = ''
    else
        cur = string.sub(v, 1, sep - 1)
        prev = string.sub(v, sep + 1)
    end
    if ARGV[1] == cur or (prev ~= '' and ARGV[1] == prev) then
        redis.call('SET', KEYS[1], ARGV[2] .. '|' .. cur, 'EX', tonumber(ARGV[3]))
        return 1
    end
    return -1
    """

    async def rotate_refresh_session(
        self, user: User, sid: str, presented_jti: str
    ) -> tuple[str, str]:
        """
        Rotate one session's refresh token, lock-free, with reuse detection.

        The presented jti must be the session's current jti or its immediate predecessor
        (a one-rotation grace that lets two browser tabs sharing the cookie both refresh
        without one revoking the other). A jti older than that is treated as reuse of a stolen
        chain and revokes the session. An unknown/logged-out session just 401s — its key is
        already gone, so there is nothing to revoke.
        """
        key = self._refresh_key(str(user.id), sid)
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

        # Mint the next token up front so the CAS can install its jti atomically.
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
        new_refresh, new_jti = create_refresh_token(
            user_id=str(user.id), school_id=str(user.school_id), sid=sid
        )

        result = int(await self.redis.eval(self._ROTATE_LUA, 1, key, presented_jti, new_jti, ttl))
        if result == 1:
            # Rotated (current jti, or the predecessor within the grace window). We do NOT
            # blacklist the presented jti: the atomic CAS already makes a superseded token
            # unusable, and blacklisting it would break the legitimate predecessor grace.
            return access_token, new_refresh
        if result == 0:
            # Session no longer exists (logged out / expired). Key is gone — nothing to revoke.
            raise ValueError("Session expired, please log in again")
        # result == -1: a jti older than the one-rotation grace → reuse of a stolen chain.
        # Revoke the whole session so it can't continue.
        await self.blacklist_token(presented_jti, ttl)
        await self.redis.delete(key)
        raise ValueError("Refresh token reuse detected")

    async def revoke_session(self, user_id: str, sid: str) -> None:
        """Log out a single device/session (drop its refresh slot)."""
        await self.redis.delete(self._refresh_key(user_id, sid))

    async def revoke_all_sessions(self, user_id: str) -> None:
        """Log out everywhere — drop every refresh session for the user."""
        pattern = f"{settings.REDIS_REFRESH_JTI_PREFIX}{user_id}:*"
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)

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
