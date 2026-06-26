"""AI telemetry — structured events, request context, Prometheus metrics."""
from app.modules.ai.telemetry.context import (
    AITelemetryContext,
    bind_ai_context,
    get_ai_context,
    reset_ai_context,
)
from app.modules.ai.telemetry.events import classify_llm_error, emit_llm_call, emit_tts_call
from app.modules.ai.telemetry.metrics import ai_metrics

__all__ = [
    "AITelemetryContext",
    "ai_metrics",
    "bind_ai_context",
    "classify_llm_error",
    "emit_llm_call",
    "emit_tts_call",
    "get_ai_context",
    "reset_ai_context",
]
