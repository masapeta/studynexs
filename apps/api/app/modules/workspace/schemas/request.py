"""Workspace request schemas for the Phase 0 teacher copilot."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.ai.gateway.input_guard import sanitize_prompt_text


class WorkspaceTurnRequest(BaseModel):
    """Text-only teacher read-mode request."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["read"] = "read"
    text: str = Field(..., strict=True, min_length=1, max_length=6000)
    session_id: uuid.UUID | None = None

    @field_validator("text")
    @classmethod
    def _sanitize_text(cls, value: str) -> str:
        cleaned = sanitize_prompt_text(value, max_length=6000, field_name="text")
        if not cleaned:
            raise ValueError("text is required")
        return cleaned
