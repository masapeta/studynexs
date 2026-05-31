"""OpenAI adapter. SDK imported lazily; needs a live smoke test with a key."""
from __future__ import annotations

import time

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult

settings = get_settings()


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        from openai import AsyncOpenAI

        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
        )

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResult:
        convo = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict = {
            "model": model,
            "messages": convo,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.perf_counter()
        resp = await self._client.chat.completions.create(**kwargs)
        latency_ms = int((time.perf_counter() - start) * 1000)

        usage = getattr(resp, "usage", None)
        return LLMResult(
            text=resp.choices[0].message.content or "",
            provider=self.name,
            model=model,
            tokens_in=getattr(usage, "prompt_tokens", 0) or 0,
            tokens_out=getattr(usage, "completion_tokens", 0) or 0,
            latency_ms=latency_ms,
            raw=resp,
        )
