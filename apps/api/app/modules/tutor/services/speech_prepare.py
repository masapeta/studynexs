"""Turn lesson narration into paced teacher-style speech (SSML for Neural TTS)."""
from __future__ import annotations

import html
import re

from app.core.config import get_settings

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Slower on explain / visual steps so it feels like teaching, not reading aloud.
_STEP_RATE: dict[str, str] = {
    "what went wrong": "-10%",
    "teacher explains": "-16%",
    "see it visually": "-14%",
    "worked example": "-15%",
    "try yourself": "-12%",
    "practice": "-12%",
    "remember": "-13%",
}


def rate_for_step_title(title: str | None) -> str:
    settings = get_settings()
    base = (settings.TUTOR_TTS_RATE or "-12%").strip()
    if not title:
        return base
    return _STEP_RATE.get(title.strip().lower(), base)


def _split_sentences(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    parts = _SENTENCE_SPLIT.split(cleaned)
    return [p.strip() for p in parts if p.strip()]


def prepare_teacher_speech_text(narration: str) -> str:
    """Plain text for edge-tts — pauses via paragraph breaks, no XML (edge escapes tags)."""
    sentences = _split_sentences(narration)
    if not sentences:
        return narration.strip()
    return "\n\n".join(sentences)


def build_teacher_ssml(narration: str, voice: str, *, rate: str | None = None) -> str:
    """Full SSML for Azure Speech only."""
    settings = get_settings()
    speech_rate = (rate or settings.TUTOR_TTS_RATE or "-12%").strip()
    pitch = (settings.TUTOR_TTS_PITCH or "+0Hz").strip()

    sentences = _split_sentences(narration)
    if not sentences:
        sentences = [narration.strip()]

    chunks: list[str] = []
    for sent in sentences:
        safe = html.escape(sent)
        if sent.endswith("?"):
            safe = f"<prosody pitch='+3Hz'>{safe}</prosody>"
        chunks.append(safe)

    body = '<break time="550ms"/>'.join(chunks)

    return (
        "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-IN'>"
        f"<voice xml:lang='en-IN' name='{html.escape(voice, quote=True)}'>"
        f"<prosody rate='{html.escape(speech_rate, quote=True)}' "
        f"pitch='{html.escape(pitch, quote=True)}'>"
        f"{body}"
        "</prosody></voice></speak>"
    )
