"""Provider-agnostic LLM gateway — the single place the app calls an LLM.

Usage:
    from app.modules.ai.gateway import generate_llm, record_usage, LLMMessage

    result = await generate_llm([LLMMessage("user", "...")])
    await record_usage(db, feature="question_paper", result=result, school_id=..., created_by=...)
"""
from app.modules.ai.gateway.base import LLMImage, LLMMessage, LLMProvider, LLMResult
from app.modules.ai.gateway.factory import default_model, get_provider
from app.modules.ai.gateway.invoke import generate_llm
from app.modules.ai.gateway.metering import record_usage

__all__ = [
    "LLMImage",
    "LLMMessage",
    "LLMProvider",
    "LLMResult",
    "get_provider",
    "default_model",
    "generate_llm",
    "record_usage",
]
