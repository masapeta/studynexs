"""Ollama adapter — local or cloud models via the Ollama HTTP API."""
from __future__ import annotations

import base64
import time
from typing import Any

import httpx
import structlog

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult

settings = get_settings()
logger = structlog.get_logger()


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        base = (settings.OLLAMA_BASE_URL or "").strip().rstrip("/")
        if not base:
            raise RuntimeError("OLLAMA_BASE_URL is not configured")
        self._base_url = base
        self._api_key = (settings.OLLAMA_API_KEY or "").strip()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        convo: list[dict[str, Any]] = []
        for m in messages:
            entry: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.images:
                entry["images"] = [
                    base64.b64encode(img.data).decode("ascii") for img in m.images
                ]
            convo.append(entry)
        return convo

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResult:
        resolved_model = model or settings.OLLAMA_MODEL
        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": self._build_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        start = time.perf_counter()
        async with httpx.AsyncClient(
            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
        ) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = int((time.perf_counter() - start) * 1000)
        message = data.get("message") or {}
        text = message.get("content") or ""
        if not text.strip():
            raise RuntimeError("Ollama returned an empty response")

        prompt_tokens = int((data.get("prompt_eval_count") or 0))
        completion_tokens = int((data.get("eval_count") or 0))

        return LLMResult(
            text=text,
            provider=self.name,
            model=resolved_model,
            tokens_in=prompt_tokens,
            tokens_out=completion_tokens,
            latency_ms=latency_ms,
            raw=data,
        )
