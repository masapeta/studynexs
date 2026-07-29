"""Primary LLM invocation with optional fallback provider (e.g. OpenAI → Ollama)."""
from __future__ import annotations

import time

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMResult
from app.modules.ai.gateway.factory import default_model, get_provider
from app.modules.ai.telemetry import classify_llm_error, emit_llm_call
from app.modules.ai.telemetry.otel_bridge import llm_span

settings = get_settings()


def _fallback_provider_name(explicit: str | None = None) -> str | None:
    name = (explicit or settings.AI_FALLBACK_PROVIDER or "").strip().lower()
    if not name:
        return None
    if name == "ollama" and not (settings.OLLAMA_BASE_URL or "").strip():
        return None
    return name


def _fallback_model(provider: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    configured = (settings.AI_FALLBACK_MODEL or "").strip()
    if configured:
        return configured
    return default_model(provider)


async def generate_llm(
    messages: list[LLMMessage],
    *,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    json_mode: bool = False,
    provider_name: str | None = None,
    fallback_provider_name: str | None = None,
    fallback_model: str | None = None,
    feature: str | None = None,
    caller: str | None = None,
) -> LLMResult:
    """Call the configured primary provider; on failure try fallback (e.g. Ollama gemma4)."""
    primary = (provider_name or settings.AI_DEFAULT_PROVIDER).lower()
    primary_model = model or default_model(primary)
    primary_provider = get_provider(primary)
    call_started = time.perf_counter()

    with llm_span(
        feature=feature,
        primary_provider=primary,
        model=primary_model,
        caller=caller,
    ):
        try:
            result = await primary_provider.generate(
                messages,
                model=primary_model,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
            result.primary_provider = primary
            result.used_fallback = False
            emit_llm_call(
                status="success",
                feature=feature,
                provider=result.provider,
                model=result.model,
                latency_ms=result.latency_ms,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                primary_provider=primary,
                used_fallback=False,
                json_mode=json_mode,
                max_tokens=max_tokens,
                caller=caller,
            )
            return result
        except Exception as primary_exc:
            fallback = _fallback_provider_name(fallback_provider_name)
            if not fallback or fallback == primary:
                latency_ms = int((time.perf_counter() - call_started) * 1000)
                emit_llm_call(
                    status="error",
                    feature=feature,
                    provider=primary,
                    model=primary_model,
                    latency_ms=latency_ms,
                    primary_provider=primary,
                    error_type=classify_llm_error(primary_exc),
                    json_mode=json_mode,
                    max_tokens=max_tokens,
                    caller=caller,
                )
                raise

            fb_provider = get_provider(fallback)
            fb_model = _fallback_model(fallback, fallback_model)
            try:
                result = await fb_provider.generate(
                    messages,
                    model=fb_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
                result.primary_provider = primary
                result.used_fallback = True
                emit_llm_call(
                    status="fallback_success",
                    feature=feature,
                    provider=result.provider,
                    model=result.model,
                    latency_ms=result.latency_ms,
                    tokens_in=result.tokens_in,
                    tokens_out=result.tokens_out,
                    primary_provider=primary,
                    used_fallback=True,
                    json_mode=json_mode,
                    max_tokens=max_tokens,
                    caller=caller,
                )
                return result
            except Exception as fallback_exc:
                latency_ms = int((time.perf_counter() - call_started) * 1000)
                emit_llm_call(
                    status="error",
                    feature=feature,
                    provider=fallback,
                    model=fb_model,
                    latency_ms=latency_ms,
                    primary_provider=primary,
                    used_fallback=True,
                    error_type=classify_llm_error(fallback_exc),
                    json_mode=json_mode,
                    max_tokens=max_tokens,
                    caller=caller,
                )
                raise fallback_exc from primary_exc
