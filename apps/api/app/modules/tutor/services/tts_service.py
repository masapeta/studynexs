"""Neural text-to-speech for the AI tutor.

Supports two backends:
- **Azure Speech** — production path when AZURE_SPEECH_KEY is set (paid, SLA, Indian region).
- **Edge TTS** — same Microsoft Neural voices via edge-tts, no API key (ideal for pilot/demo).

When neither is available, `tts_enabled()` is False and the client falls back to Web Speech.
"""
from __future__ import annotations

import html
import io
import time
from typing import Literal

import httpx

from app.core.config import get_settings
from app.modules.ai.gateway.input_guard import sanitize_tts_voice
from app.modules.ai.telemetry import classify_llm_error, emit_tts_call

settings = get_settings()

TtsBackend = Literal["azure", "edge", "off"]


def _edge_tts_importable() -> bool:
    try:
        import edge_tts  # noqa: F401

        return True
    except ImportError:
        return False


def _azure_configured() -> bool:
    return bool(settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION)


def resolve_tts_backend() -> TtsBackend:
    mode = (settings.TUTOR_TTS_PROVIDER or "auto").strip().lower()
    if mode == "off":
        return "off"
    if mode == "azure":
        return "azure" if _azure_configured() else "off"
    if mode == "edge":
        return "edge" if _edge_tts_importable() else "off"
    # auto — prefer Azure in production setups, Edge for zero-config pilot
    if _azure_configured():
        return "azure"
    if _edge_tts_importable():
        return "edge"
    return "off"


def tts_enabled() -> bool:
    return resolve_tts_backend() != "off"


def default_tts_voice() -> str:
    return settings.AZURE_SPEECH_VOICE


def _ssml(text: str, voice: str) -> str:
    safe = html.escape(text)
    return (
        "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-IN'>"
        f"<voice xml:lang='en-IN' name='{html.escape(voice, quote=True)}'>"
        f"<prosody rate='-8%'>{safe}</prosody>"
        "</voice></speak>"
    )


async def _synthesize_azure(text: str, voice: str) -> bytes:
    url = f"https://{settings.AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "studynexs-tutor",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, content=_ssml(text, voice).encode("utf-8"))
    resp.raise_for_status()
    return resp.content


async def _synthesize_edge(text: str, voice: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=settings.TUTOR_TTS_RATE)
    buf = io.BytesIO()
    async for message in communicate.stream():
        if message["type"] == "audio":
            buf.write(message["data"])
    audio = buf.getvalue()
    if not audio:
        raise RuntimeError("Edge TTS returned no audio")
    return audio


async def synthesize_speech(text: str, voice: str | None = None) -> bytes:
    """Return MP3 audio bytes for `text`. Raises RuntimeError if TTS is not configured."""
    backend = resolve_tts_backend()
    if backend == "off":
        raise RuntimeError("TTS is not configured")

    voice = sanitize_tts_voice(voice, default=default_tts_voice())
    started = time.perf_counter()
    try:
        if backend == "azure":
            audio = await _synthesize_azure(text, voice)
        else:
            audio = await _synthesize_edge(text, voice)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        emit_tts_call(
            status="error",
            chars=len(text),
            latency_ms=latency_ms,
            voice=voice,
            error_type=classify_llm_error(exc),
        )
        raise
    latency_ms = int((time.perf_counter() - started) * 1000)
    emit_tts_call(status="success", chars=len(text), latency_ms=latency_ms, voice=voice)
    return audio
