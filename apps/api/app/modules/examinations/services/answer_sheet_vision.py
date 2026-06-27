"""Vision OCR — extract per-question student answers from an answer-sheet image."""
from __future__ import annotations

import json
import re

import structlog

from app.core.config import get_settings
from app.modules.ai.gateway import LLMImage, LLMMessage, default_model, generate_llm
from app.modules.ai.gateway.base import LLMResult
from app.modules.ai.gateway.factory import ollama_configured
from app.modules.files.services.file_validation import IMAGE_MIMES, normalize_mime

logger = structlog.get_logger()
settings = get_settings()

_VISION_PROVIDERS = frozenset({"gemini", "openai", "ollama"})


def _ollama_ready() -> bool:
    return ollama_configured()


def _vision_fallback_provider() -> str | None:
    """Answer-sheet handwriting fallback — Ollama gemma4 by default (not a second OpenAI call)."""
    for candidate in (
        (settings.AI_VISION_FALLBACK_PROVIDER or "").strip().lower(),
        (settings.AI_FALLBACK_PROVIDER or "").strip().lower(),
        "ollama",
    ):
        if not candidate:
            continue
        if candidate == "ollama" and not _ollama_ready():
            continue
        return candidate
    return None


def _vision_primary_provider() -> str | None:
    """First vision attempt: Gemini if configured, else AI_DEFAULT_PROVIDER when vision-capable."""
    if settings.GEMINI_API_KEY:
        return "gemini"
    primary = (settings.AI_DEFAULT_PROVIDER or "").strip().lower()
    if primary in _VISION_PROVIDERS:
        if primary == "ollama" and not _ollama_ready():
            return None
        if primary == "openai" and not settings.OPENAI_API_KEY:
            return None
        if primary == "gemini" and not settings.GEMINI_API_KEY:
            return None
        return primary
    if settings.OPENAI_API_KEY:
        return "openai"
    if _ollama_ready():
        return "ollama"
    return None


def vision_llm_available() -> bool:
    return _vision_primary_provider() is not None or _vision_fallback_provider() is not None


def is_image_mime(mime: str) -> bool:
    return normalize_mime(mime) in IMAGE_MIMES


def _question_prompt(question_schema: list[dict], rubrics: dict[str, dict]) -> str:
    lines = [
        "Transcribe the student's handwritten or typed answers from this answer sheet.",
        "Return JSON only: {\"answers\": {\"<question_number>\": \"<transcribed text>\"}}",
        "Use empty string when a question is blank or illegible.",
        "",
        "Questions on this exam:",
    ]
    for q in question_schema:
        qno = str(q["no"])
        rubric = rubrics.get(qno, {})
        qtext = str(rubric.get("question_text") or "")[:200]
        lines.append(f"- Q{qno} ({q.get('max_marks')} marks): {qtext}")
    return "\n".join(lines)


def _parse_answers_json(text: str) -> dict[str, str]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("vision_json_parse_failed")
        return {}
    answers = data.get("answers") if isinstance(data, dict) else data
    if not isinstance(answers, dict):
        return {}
    return {str(k): str(v) for k, v in answers.items()}


def _ollama_vision_model() -> str:
    return (settings.OLLAMA_VISION_MODEL or settings.OLLAMA_MODEL or "gemma4:cloud").strip()


async def extract_answers_from_image(
    *,
    image_bytes: bytes,
    mime_type: str,
    question_schema: list[dict],
    rubrics: dict[str, dict],
) -> tuple[dict[str, str], LLMResult | None]:
    """OCR via vision LLM. Primary provider first, then Ollama gemma4 for handwriting."""
    if not vision_llm_available():
        return {}, None
    if not is_image_mime(mime_type):
        return {}, None

    primary = _vision_primary_provider()
    fallback = _vision_fallback_provider()
    if not primary and fallback:
        primary = fallback
        fallback = None
    if not primary:
        return {}, None

    prompt = _question_prompt(question_schema, rubrics)
    messages = [
        LLMMessage(
            role="user",
            content=prompt,
            images=[LLMImage(data=image_bytes, mime_type=mime_type.split(";")[0])],
        )
    ]
    fb_model = _ollama_vision_model() if fallback == "ollama" else None
    try:
        result = await generate_llm(
            messages,
            model=default_model(primary),
            provider_name=primary,
            fallback_provider_name=fallback,
            fallback_model=fb_model,
            temperature=0.1,
            max_tokens=4096,
            json_mode=True,
            feature="answer_sheet_vision",
            caller="extract_answers_from_image",
        )
    except (RuntimeError, ValueError):
        logger.warning("answer_sheet_vision_failed", primary=primary, fallback=fallback)
        return {}, None
    return _parse_answers_json(result.text), result
