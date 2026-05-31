"""Provider-agnostic LLM gateway — the single place the app calls an LLM.

Usage:
    from app.modules.ai.gateway import get_provider, default_model, record_usage, LLMMessage

    provider = get_provider()                 # or get_provider("anthropic")
    result = await provider.generate([LLMMessage("user", "...")], model=default_model())
    await record_usage(db, feature="question_paper", result=result, school_id=..., created_by=...)
"""
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult
from app.modules.ai.gateway.factory import default_model, get_provider
from app.modules.ai.gateway.metering import record_usage

__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResult",
    "get_provider",
    "default_model",
    "record_usage",
]
