"""Neural text-to-speech for the AI tutor — Azure Speech (soft female Indian voice).

Optional: when AZURE_SPEECH_KEY is unset, `tts_enabled()` is False and the client
falls back to the browser's Web Speech voice. Synthesis is on-demand per lesson step
(short narration), so cost stays small.
"""
from __future__ import annotations

import html
import time

import httpx

from app.core.config import get_settings
from app.modules.ai.telemetry import classify_llm_error, emit_tts_call

settings = get_settings()


def tts_enabled() -> bool:
    return bool(settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION)


def _ssml(text: str, voice: str) -> str:
    # html.escape keeps student/narration text XML-safe inside the SSML body.
    safe = html.escape(text)
    return (
        "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-IN'>"
        f"<voice xml:lang='en-IN' name='{html.escape(voice, quote=True)}'>"
        f"<prosody rate='-8%'>{safe}</prosody>"
        "</voice></speak>"
    )


async def synthesize_speech(text: str, voice: str | None = None) -> bytes:
    """Return MP3 audio bytes for `text`. Raises RuntimeError if not configured."""
    if not tts_enabled():
        raise RuntimeError("Azure Speech is not configured")
    voice = voice or settings.AZURE_SPEECH_VOICE
    url = f"https://{settings.AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "studynexs-tutor",
    }
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, content=_ssml(text, voice).encode("utf-8"))
        resp.raise_for_status()
        audio = resp.content
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
