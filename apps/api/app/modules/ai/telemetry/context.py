"""Request-scoped AI telemetry context (correlation IDs, tenant, feature)."""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class AITelemetryContext:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    school_id: str | None = None
    user_id: str | None = None
    feature: str | None = None
    endpoint: str | None = None


_ai_ctx: ContextVar[AITelemetryContext | None] = ContextVar("ai_telemetry_ctx", default=None)


def get_ai_context() -> AITelemetryContext:
    ctx = _ai_ctx.get()
    if ctx is None:
        ctx = AITelemetryContext()
        _ai_ctx.set(ctx)
    return ctx


def bind_ai_context(**kwargs: str | None) -> AITelemetryContext:
    """Merge fields into the current telemetry context."""
    ctx = get_ai_context()
    for key, value in kwargs.items():
        if value is not None and hasattr(ctx, key):
            setattr(ctx, key, value)
    return ctx


def reset_ai_context() -> None:
    _ai_ctx.set(None)
