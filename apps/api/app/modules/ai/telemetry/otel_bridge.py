"""Export AI telemetry to OpenTelemetry metrics and spans."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.otel import get_meter, get_tracer, otel_enabled

_meter = None
_tracer = None
_llm_requests = None
_llm_tokens_in = None
_llm_tokens_out = None
_llm_latency = None
_llm_fallbacks = None
_tts_requests = None
_tts_latency = None


def _init_instruments() -> None:
    global _meter, _tracer, _llm_requests, _llm_tokens_in, _llm_tokens_out
    global _llm_latency, _llm_fallbacks, _tts_requests, _tts_latency
    if _meter is not None:
        return
    _meter = get_meter("studynexs.ai")
    _tracer = get_tracer("studynexs.ai")
    _llm_requests = _meter.create_counter(
        "studynexs.ai.llm.requests",
        description="LLM calls by feature, provider, model, and status",
    )
    _llm_tokens_in = _meter.create_counter(
        "studynexs.ai.llm.tokens.input",
        description="LLM input tokens",
    )
    _llm_tokens_out = _meter.create_counter(
        "studynexs.ai.llm.tokens.output",
        description="LLM output tokens",
    )
    _llm_latency = _meter.create_histogram(
        "studynexs.ai.llm.latency",
        description="LLM call latency",
        unit="ms",
    )
    _llm_fallbacks = _meter.create_counter(
        "studynexs.ai.llm.fallback_success",
        description="LLM calls that succeeded via fallback provider",
    )
    _tts_requests = _meter.create_counter(
        "studynexs.ai.tts.requests",
        description="Tutor TTS synthesis calls",
    )
    _tts_latency = _meter.create_histogram(
        "studynexs.ai.tts.latency",
        description="TTS call latency",
        unit="ms",
    )


def _attrs(
    *,
    feature: str,
    provider: str,
    model: str,
    status: str,
    primary_provider: str | None = None,
) -> dict[str, str]:
    labels = {
        "feature": feature,
        "provider": provider,
        "model": model,
        "status": status,
    }
    if primary_provider:
        labels["primary_provider"] = primary_provider
    return labels


def record_llm_otel(
    *,
    status: str,
    feature: str,
    provider: str,
    model: str,
    latency_ms: int = 0,
    tokens_in: int = 0,
    tokens_out: int = 0,
    primary_provider: str | None = None,
    used_fallback: bool = False,
    error_type: str | None = None,
    caller: str | None = None,
) -> None:
    if not otel_enabled(get_settings()):
        return
    try:
        _init_instruments()
        attrs = _attrs(
            feature=feature,
            provider=provider,
            model=model,
            status=status,
            primary_provider=primary_provider,
        )
        if error_type:
            attrs["error_type"] = error_type
        if caller:
            attrs["caller"] = caller

        _llm_requests.add(1, attrs)
        if tokens_in:
            _llm_tokens_in.add(tokens_in, attrs)
        if tokens_out:
            _llm_tokens_out.add(tokens_out, attrs)
        if latency_ms > 0:
            _llm_latency.record(latency_ms, attrs)
        if used_fallback and status != "error":
            _llm_fallbacks.add(1, attrs)
    except Exception:
        return


def record_tts_otel(
    *,
    status: str,
    latency_ms: int = 0,
    voice: str | None = None,
    error_type: str | None = None,
) -> None:
    if not otel_enabled(get_settings()):
        return
    try:
        _init_instruments()
        attrs: dict[str, str] = {"status": status}
        if voice:
            attrs["voice"] = voice
        if error_type:
            attrs["error_type"] = error_type
        _tts_requests.add(1, attrs)
        if latency_ms > 0:
            _tts_latency.record(latency_ms, attrs)
    except Exception:
        # Telemetry must never break tutor TTS or other user-facing AI paths.
        return


def llm_span(
    *,
    feature: str | None,
    primary_provider: str,
    model: str,
    caller: str | None = None,
):
    """Context manager factory for an LLM generate span."""
    if not otel_enabled(get_settings()):
        from contextlib import nullcontext

        return nullcontext()
    _init_instruments()
    attributes: dict[str, str] = {
        "ai.feature": feature or "unknown",
        "ai.primary_provider": primary_provider,
        "ai.model": model,
    }
    if caller:
        attributes["ai.caller"] = caller
    return _tracer.start_as_current_span("ai.llm.generate", attributes=attributes)
