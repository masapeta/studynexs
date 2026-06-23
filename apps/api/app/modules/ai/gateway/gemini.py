"""Google Gemini adapter (google-genai SDK). SDK imported lazily; needs a live smoke test.

API surface for google-genai can shift between versions — verify
`client.aio.models.generate_content(...)` and usage_metadata field names against the
installed SDK during the benchmark.
"""
from __future__ import annotations

import time

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult

settings = get_settings()


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        from google import genai

        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResult:
        from google.genai import types

        system = "\n".join(m.content for m in messages if m.role == "system") or None
        contents: list = []
        for m in messages:
            if m.role == "system":
                continue
            parts: list = []
            for img in m.images or []:
                parts.append(types.Part.from_bytes(data=img.data, mime_type=img.mime_type))
            if m.content:
                parts.append(types.Part.from_text(text=m.content))
            if len(parts) == 1:
                contents.append(parts[0])
            elif parts:
                contents.append(types.Content(role="user", parts=parts))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system,
            response_mime_type="application/json" if json_mode else None,
        )

        start = time.perf_counter()
        resp = await self._client.aio.models.generate_content(
            model=model, contents=contents, config=config
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        usage = getattr(resp, "usage_metadata", None)
        return LLMResult(
            text=getattr(resp, "text", "") or "",
            provider=self.name,
            model=model,
            tokens_in=getattr(usage, "prompt_token_count", 0) or 0,
            tokens_out=getattr(usage, "candidates_token_count", 0) or 0,
            latency_ms=latency_ms,
            raw=resp,
        )
