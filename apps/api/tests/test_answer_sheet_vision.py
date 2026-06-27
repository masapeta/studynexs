"""Answer-sheet vision — Ollama gemma4 fallback for handwriting OCR."""
from __future__ import annotations

import pytest

from app.modules.ai.gateway.base import LLMImage, LLMMessage, LLMResult
from app.modules.examinations.services import answer_sheet_vision as vision


def test_vision_fallback_defaults_to_ollama(monkeypatch):
    monkeypatch.setattr(vision.settings, "AI_VISION_FALLBACK_PROVIDER", "")
    monkeypatch.setattr(vision.settings, "AI_FALLBACK_PROVIDER", "")
    monkeypatch.setattr(vision.settings, "OLLAMA_BASE_URL", "https://ollama.com")
    assert vision._vision_fallback_provider() == "ollama"


def test_vision_primary_prefers_gemini(monkeypatch):
    monkeypatch.setattr(vision.settings, "GEMINI_API_KEY", "key")
    monkeypatch.setattr(vision.settings, "AI_DEFAULT_PROVIDER", "openai")
    assert vision._vision_primary_provider() == "gemini"


@pytest.mark.asyncio
async def test_extract_answers_falls_back_to_ollama(monkeypatch):
    primary = type("P", (), {})()
    fallback = type("P", (), {})()

    async def primary_fail(*_a, **_k):
        raise RuntimeError("openai vision down")

    async def fallback_ok(*_a, **_k):
        return LLMResult(
            text='{"answers": {"1": "hello"}}',
            provider="ollama",
            model="gemma4:cloud",
            tokens_in=10,
            tokens_out=20,
            latency_ms=100,
        )

    primary.generate = primary_fail
    fallback.generate = fallback_ok

    calls: list[dict] = []

    async def fake_generate_llm(*_args, **kwargs):
        calls.append(kwargs)
        from app.modules.ai.gateway import invoke as inv

        return await inv.generate_llm(*_args, **kwargs)

    monkeypatch.setattr(vision, "generate_llm", fake_generate_llm)
    monkeypatch.setattr(vision, "_vision_primary_provider", lambda: "openai")
    monkeypatch.setattr(vision, "_vision_fallback_provider", lambda: "ollama")
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.get_provider",
        lambda name: primary if name == "openai" else fallback,
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.settings.AI_FALLBACK_PROVIDER",
        "ollama",
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.settings.OLLAMA_BASE_URL",
        "https://ollama.com",
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.default_model",
        lambda p=None: "gemma4:cloud" if p == "ollama" else "gpt-4o",
    )

    answers, result = await vision.extract_answers_from_image(
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
        question_schema=[{"no": 1, "max_marks": 2}],
        rubrics={"1": {"question_text": "Define algebra"}},
    )
    assert answers == {"1": "hello"}
    assert result is not None
    assert result.used_fallback is True
    assert result.provider == "ollama"
    assert calls[0]["fallback_provider_name"] == "ollama"
    assert calls[0]["fallback_model"] == "gemma4:cloud"
