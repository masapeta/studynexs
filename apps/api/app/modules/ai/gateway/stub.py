"""Development stub — drafts placeholder text when no LLM API key is configured."""
from __future__ import annotations

import re

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult

settings = get_settings()


def _draft_remark(messages: list[LLMMessage]) -> str:
    user = next((m.content for m in reversed(messages) if m.role == "user"), "")
    match = re.search(r"Student:\s*(.+)", user)
    name = match.group(1).split("(")[0].strip() if match else "The student"
    return (
        f"{name} has shown steady effort this term. Marks reflect strengths in some "
        f"subjects and room to grow in others — regular revision and practice will help. "
        f"Parents are encouraged to support consistent study habits at home. "
        f"(Dev draft — set an AI provider API key for personalised remarks.)"
    )


class StubProvider(LLMProvider):
    name = "stub"

    def __init__(self) -> None:
        if settings.is_production:
            raise RuntimeError("Stub AI provider is disabled in production")

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResult:
        if json_mode:
            text = '{"sections": []}'
        else:
            text = _draft_remark(messages)
        return LLMResult(
            text=text,
            provider=self.name,
            model=model or "dev-stub",
            tokens_in=120,
            tokens_out=80,
            latency_ms=1,
        )
