"""Application-level field encryption for regulated PII (e.g. Aadhaar numbers).

Design goals (owner direction): production-ready, configurable key management, and a
backward-compatible rollout — existing plaintext rows must keep reading while new writes are
encrypted, so the schema migration can be a simple, reversible column-widen with no risky
in-place data transform.

Key management
--------------
Keys come from ``settings.AADHAAR_ENCRYPTION_KEYS`` (a list of urlsafe-base64 Fernet keys).
The FIRST key encrypts; ALL keys can decrypt — so rotation is: prepend a new key, redeploy,
optionally re-encrypt in the background, then drop the old key. Generate a key with
``python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"``
and store it in the secret store (never in git). A production boot guardrail (config.py)
refuses to start production without at least one key.

Backward compatibility
----------------------
``EncryptedString`` decrypts on read; if a stored value isn't a valid token (a legacy
plaintext row, or encryption not configured) it is returned verbatim. With no keys configured
(local dev) values are stored as-is — the column type is transparent, so dev keeps working.
"""
from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings


@lru_cache
def _cipher() -> MultiFernet | None:
    """Build a MultiFernet from configured keys, or None if encryption is disabled (dev)."""
    keys = [k.strip() for k in get_settings().AADHAAR_ENCRYPTION_KEYS if k.strip()]
    if not keys:
        return None
    return MultiFernet([Fernet(k.encode()) for k in keys])


def encrypt_value(plaintext: str | None) -> str | None:
    """Encrypt a value for storage. Returns plaintext unchanged when encryption is disabled."""
    if plaintext is None:
        return None
    cipher = _cipher()
    if cipher is None:
        return plaintext
    return cipher.encrypt(plaintext.encode()).decode()


def decrypt_value(stored: str | None) -> str | None:
    """Decrypt a stored value. A non-token (legacy plaintext, or disabled) is returned as-is."""
    if stored is None:
        return None
    cipher = _cipher()
    if cipher is None:
        return stored
    try:
        return cipher.decrypt(stored.encode()).decode()
    except (InvalidToken, ValueError):
        # Legacy plaintext written before encryption was enabled — read it through unchanged.
        return stored


class EncryptedString(TypeDecorator):
    """A String column whose value is transparently encrypted at rest.

    Stores the Fernet token (or plaintext when encryption is disabled). ``length`` sizes the
    underlying column for the ciphertext, not the plaintext — a Fernet token is well under
    512 chars for short PII like a 12-digit Aadhaar number.
    """

    impl = String
    cache_ok = True

    def __init__(self, length: int = 512, **kwargs) -> None:
        super().__init__(length=length, **kwargs)

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        return encrypt_value(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return decrypt_value(value)
