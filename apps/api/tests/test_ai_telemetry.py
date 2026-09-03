"""AI telemetry — metrics registry, gateway events, fallback tracking."""
from __future__ import annotations

import pytest

from app.modules.ai.gateway.base import LLMMessage, LLMResult
from app.modules.ai.telemetry import ai_metrics, classify_llm_error, emit_llm_call
from app.modules.ai.telemetry.metrics import AIMetricsRegistry


def test_classify_llm_error_timeout():
    assert classify_llm_error(TimeoutError("slow")) == "timeout"


def test_emit_llm_call_updates_metrics():
    emit_llm_call(
        status="success",
        feature="question_paper",
        provider="openai",
        model="gpt-4o-mini",
        latency_ms=120,
        tokens_in=100,
        tokens_out=50,
    )
    # Global registry also updated — check shape
    snap = ai_metrics.snapshot()
    assert snap["llm_requests_total"] >= 1
    assert "question_paper" in snap["by_feature"]


def test_prometheus_text_includes_counters():
    registry = AIMetricsRegistry()
    registry.record_llm_call(
        feature="report_card",
        provider="ollama",
        model="gemma4:cloud",
        status="fallback_success",
        latency_ms=200,
        tokens_in=10,
        tokens_out=20,
        used_fallback=True,
    )
    text = registry.prometheus_text()
    assert "studynexs_ai_llm_requests_total" in text
    assert "report_card" in text
    assert "studynexs_ai_llm_fallback_success_total" in text


@pytest.mark.asyncio
async def test_generate_llm_emits_fallback_telemetry(monkeypatch):
    from app.modules.ai.gateway import invoke as inv

    primary = type("P", (), {})()
    fallback = type("P", (), {})()

    async def primary_fail(*_a, **_k):
        raise RuntimeError("openai down")

    async def fallback_ok(*_a, **_k):
        return LLMResult(
            text="ok",
            provider="ollama",
            model="gemma4:cloud",
            tokens_in=1,
            tokens_out=2,
            latency_ms=50,
        )

    primary.generate = primary_fail
    fallback.generate = fallback_ok

    def fake_get_provider(name):
        if name == "openai":
            return primary
        return fallback

    before = ai_metrics.snapshot()["llm_fallback_success_total"]
    monkeypatch.setattr(inv, "get_provider", fake_get_provider)
    monkeypatch.setattr(inv.settings, "AI_DEFAULT_PROVIDER", "openai")
    monkeypatch.setattr(inv.settings, "AI_FALLBACK_PROVIDER", "ollama")
    monkeypatch.setattr(inv.settings, "OLLAMA_BASE_URL", "https://ollama.com")
    monkeypatch.setattr(
        inv,
        "default_model",
        lambda p=None: "gemma4:cloud" if p == "ollama" else "gpt-4o-mini",
    )

    result = await inv.generate_llm(
        [LLMMessage("user", "hi")],
        feature="report_card",
    )
    assert result.used_fallback is True
    assert result.primary_provider == "openai"
    after = ai_metrics.snapshot()["llm_fallback_success_total"]
    assert after >= before + 1
