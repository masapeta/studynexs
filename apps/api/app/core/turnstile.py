"""Cloudflare Turnstile verification for public demo provisioning."""
from __future__ import annotations

import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


async def verify_turnstile_token(token: str, *, remote_ip: str | None = None) -> bool:
    """Return True when Turnstile accepts the token."""
    secret = settings.TURNSTILE_SECRET_KEY.strip()
    if not secret:
        return False

    payload: dict[str, str] = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data=payload,
            )
        resp.raise_for_status()
        body = resp.json()
    except Exception:
        logger.exception("turnstile_verify_failed")
        return False

    return bool(body.get("success"))
