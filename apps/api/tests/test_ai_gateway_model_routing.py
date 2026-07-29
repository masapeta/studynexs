"""AI gateway model routing for general reasoning vs OCR/vision."""
from __future__ import annotations

from app.modules.ai.gateway import factory, invoke


def test_default_model_does_not_leak_general_model_to_other_providers(monkeypatch):
    monkeypatch.setattr(factory.settings, "AI_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setattr(factory.settings, "AI_DEFAULT_MODEL", "gemma4:cloud")
    monkeypatch.setattr(factory.settings, "OLLAMA_MODEL", "gemma4:cloud")

    assert factory.default_model("ollama") == "gemma4:cloud"
    assert factory.default_model("gemini") == "gemini-1.5-flash"
    assert factory.default_model("openai") == "gpt-4o-mini"


def test_default_provider_can_have_explicit_general_model(monkeypatch):
    monkeypatch.setattr(factory.settings, "AI_DEFAULT_PROVIDER", "openai")
    monkeypatch.setattr(factory.settings, "AI_DEFAULT_MODEL", "gpt-4o")

    assert factory.default_model("openai") == "gpt-4o"
    assert factory.default_model("gemini") == "gemini-1.5-flash"


def test_general_fallback_model_uses_explicit_config(monkeypatch):
    monkeypatch.setattr(invoke.settings, "AI_FALLBACK_MODEL", "gpt-4o")

    assert invoke._fallback_model("openai") == "gpt-4o"
