"""Pydantic contracts for prospect demo sessions (Stage 2B)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DemoSessionCreateRequest(BaseModel):
    """Optional visitor label — not persisted as PII beyond the session."""

    display_name: str | None = Field(default=None, max_length=80)
    turnstile_token: str | None = Field(default=None, max_length=4096)


class DemoSessionRenewRequest(BaseModel):
    session_token: str = Field(min_length=16, max_length=512)


class DemoSessionOut(BaseModel):
    tenant_slug: str
    school_id: str
    expires_at: datetime
    access_token: str
    session_token: str
    onboarding_path: str
    school_name: str
    principal_username: str = "principal"
