"""Structured AI telemetry events — single schema for logs, metrics, and scaling signals."""
from __future__ import annotations

import structlog

from app.modules.ai.telemetry.context import get_ai_context
from app.modules.ai.telemetry.metrics import ai_metrics
from app.modules.ai.telemetry.otel_bridge import record_llm_otel, record_tts_otel

logger = structlog.get_logger()

_TIMEOUT_NAMES = frozenset({
    "APITimeoutError",
    "TimeoutError",
    "ReadTimeout",
    "ConnectTimeout",
    "WriteTimeout",
    "PoolTimeout",
})


def classify_llm_error(exc: BaseException) -> str:
    name = type(exc).__name__
    if name in _TIMEOUT_NAMES:
        return "timeout"
    if isinstance(exc, ValueError):
        return "validation"
    if isinstance(exc, RuntimeError):
        msg = str(exc).lower()
        if "empty response" in msg:
            return "empty_response"
        if "not configured" in msg:
            return "not_configured"
        return "runtime"
    if name == "HTTPStatusError":
        return "http_error"
    return "provider_error"


def emit_llm_call(
    *,
    status: str,
    provider: str,
    model: str,
    feature: str | None = None,
    latency_ms: int = 0,
    tokens_in: int = 0,
    tokens_out: int = 0,
    primary_provider: str | None = None,
    used_fallback: bool = False,
    error_type: str | None = None,
    json_mode: bool = False,
    max_tokens: int | None = None,
    caller: str | None = None,
) -> None:
    """Emit one LLM telemetry event to structlog + in-process metrics."""
    ctx = get_ai_context()
    feature = feature or ctx.feature or "unknown"

    payload = {
        "telemetry": "llm_call",
        "status": status,
        "feature": feature,
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "used_fallback": used_fallback,
        "json_mode": json_mode,
        "request_id": ctx.request_id,
    }
    if ctx.school_id:
        payload["school_id"] = ctx.school_id
    if ctx.user_id:
        payload["user_id"] = ctx.user_id
    if ctx.endpoint:
        payload["endpoint"] = ctx.endpoint
    if primary_provider:
        payload["primary_provider"] = primary_provider
    if error_type:
        payload["error_type"] = error_type
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if caller:
        payload["caller"] = caller

    if status == "error":
        logger.warning("ai_llm_call", **payload)
    else:
        logger.info("ai_llm_call", **payload)

    ai_metrics.record_llm_call(
        feature=feature,
        provider=provider,
        model=model,
        status=status,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        used_fallback=used_fallback,
    )
    record_llm_otel(
        status=status,
        feature=feature,
        provider=provider,
        model=model,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        primary_provider=primary_provider,
        used_fallback=used_fallback,
        error_type=error_type,
        caller=caller,
    )


def emit_tts_call(
    *,
    status: str,
    chars: int = 0,
    latency_ms: int = 0,
    voice: str | None = None,
    error_type: str | None = None,
) -> None:
    """Azure Speech TTS — separate from LLM gateway but part of AI surface area."""
    ctx = get_ai_context()
    payload = {
        "telemetry": "tts_call",
        "status": status,
        "feature": "tutor_tts",
        "chars": chars,
        "latency_ms": latency_ms,
        "request_id": ctx.request_id,
    }
    if voice:
        payload["voice"] = voice
    if error_type:
        payload["error_type"] = error_type
    if ctx.school_id:
        payload["school_id"] = ctx.school_id

    if status == "error":
        logger.warning("ai_tts_call", **payload)
    else:
        logger.info("ai_tts_call", **payload)
    record_tts_otel(
        status=status,
        latency_ms=latency_ms,
        voice=voice,
        error_type=error_type,
    )
