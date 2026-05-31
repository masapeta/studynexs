"""LLM gateway interface + result types.

Adapters implement `LLMProvider`. Keeping one interface means cost metering, retries,
and provider swaps live in a single place — and the Phase-0 benchmark can compare
providers without touching call sites. No provider is committed yet.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    raw: Any | None = None


class LLMProvider(ABC):
    """Common interface every provider adapter implements."""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResult:
        """Generate a completion. `json_mode` requests JSON-only output when supported."""
        raise NotImplementedError
