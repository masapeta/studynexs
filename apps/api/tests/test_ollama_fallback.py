"""Ollama provider + OpenAI → Ollama fallback via generate_llm."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.ai.gateway.base import LLMMessage, LLMResult
from app.modules.ai.gateway.invoke import generate_llm


@pytest.mark.asyncio
async def test_generate_llm_falls_back_to_ollama_on_primary_failure(monkeypatch):
    primary = MagicMock()
    primary.generate = AsyncMock(side_effect=RuntimeError("openai down"))
    fallback = MagicMock()
    fallback.generate = AsyncMock(
        return_value=LLMResult(
            text="fallback ok",
            provider="ollama",
            model="gemma4:cloud",
            tokens_in=5,
            tokens_out=10,
            latency_ms=100,
        )
    )

    def fake_get_provider(name):
        if name == "openai":
            return primary
        if name == "ollama":
            return fallback
        raise ValueError(name)

    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.get_provider",
        fake_get_provider,
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.settings.AI_DEFAULT_PROVIDER",
        "openai",
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.settings.AI_FALLBACK_PROVIDER",
        "ollama",
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.settings.OLLAMA_BASE_URL",
        "http://localhost:11434",
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.default_model",
        lambda p=None: "gemma4:cloud" if p == "ollama" else "gpt-4o-mini",
    )

    result = await generate_llm([LLMMessage("user", "hi")])
    assert result.text == "fallback ok"
    assert result.provider == "ollama"
    primary.generate.assert_awaited_once()
    fallback.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_llm_raises_when_no_fallback(monkeypatch):
    primary = MagicMock()
    primary.generate = AsyncMock(side_effect=RuntimeError("openai down"))

    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.get_provider",
        lambda _name=None: primary,
    )
    monkeypatch.setattr(
        "app.modules.ai.gateway.invoke.settings.AI_FALLBACK_PROVIDER",
        "",
    )

    with pytest.raises(RuntimeError, match="openai down"):
        await generate_llm([LLMMessage("user", "hi")])
