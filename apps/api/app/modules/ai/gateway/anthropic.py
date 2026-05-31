"""Anthropic (Claude) adapter. SDK imported lazily; needs a live smoke test with a key."""
from __future__ import annotations

import time

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult

settings = get_settings()


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self) -> None:
        from anthropic import AsyncAnthropic

        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        self._client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
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
        system = "\n".join(m.content for m in messages if m.role == "system") or None
        convo = [
            {"role": "assistant" if m.role == "assistant" else "user", "content": m.content}
            for m in messages
            if m.role != "system"
        ]
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": convo,
        }
        if system:
            kwargs["system"] = system

        start = time.perf_counter()
        resp = await self._client.messages.create(**kwargs)
        latency_ms = int((time.perf_counter() - start) * 1000)

        text = "".join(
            getattr(block, "text", "") for block in resp.content
            if getattr(block, "type", None) == "text"
        )
        return LLMResult(
            text=text,
            provider=self.name,
            model=model,
            tokens_in=getattr(resp.usage, "input_tokens", 0) or 0,
            tokens_out=getattr(resp.usage, "output_tokens", 0) or 0,
            latency_ms=latency_ms,
            raw=resp,
        )
