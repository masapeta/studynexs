"""
StudyNexs Platform — Security Utilities
JWT encode/decode, password hashing, refresh token Redis ops.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


# ── Password Hashing ────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (cost factor 12)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt hash. Fail-secure on malformed hashes."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed hash — fail securely, never crash
        return False


# ── JWT Token Operations ────────────────────────────────────────────────────


def create_access_token(
    user_id: str,
    school_id: str,
    role: str,
    tenant_slug: str,
    extra_claims: dict | None = None,
) -> str:
    """Create a short-lived access token (15 min default)."""
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "school_id": school_id,
        "role": role,
        "tenant_slug": tenant_slug,
        "jti": jti,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    school_id: str,
    sid: str,
    *,
    expires_at: datetime | None = None,
) -> tuple[str, str]:
    """Create a long-lived refresh token. Returns (token, jti).

    `sid` ties the token to one login session (one device), so multiple devices each get
    their own rotation chain instead of clobbering a single per-user slot.
    """
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    exp = expires_at or (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": user_id,
        "school_id": school_id,
        "jti": jti,
        "sid": sid,
        "type": "refresh",
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
