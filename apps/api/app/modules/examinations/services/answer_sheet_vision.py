"""Vision OCR — extract per-question student answers from an answer-sheet image."""
from __future__ import annotations

import json
import re

import structlog

from app.core.config import Environment, get_settings
from app.modules.ai.gateway import LLMImage, LLMMessage, default_model, get_provider
from app.modules.ai.gateway.base import LLMResult
from app.modules.files.services.file_validation import IMAGE_MIMES, normalize_mime

logger = structlog.get_logger()
settings = get_settings()


def vision_llm_available() -> bool:
    return bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)


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


async def extract_answers_from_image(
    *,
    image_bytes: bytes,
    mime_type: str,
    question_schema: list[dict],
    rubrics: dict[str, dict],
) -> tuple[dict[str, str], LLMResult | None]:
    """OCR via vision LLM. Returns ({qno: answer}, llm_result). Empty dict when unavailable."""
    if not vision_llm_available():
        return {}, None
    if not is_image_mime(mime_type):
        return {}, None

    prompt = _question_prompt(question_schema, rubrics)
    provider_name = "gemini" if settings.GEMINI_API_KEY else "openai"
    try:
        provider = get_provider(provider_name)
    except (RuntimeError, ValueError):
        return {}, None

    messages = [
        LLMMessage(
            role="user",
            content=prompt,
            images=[LLMImage(data=image_bytes, mime_type=mime_type.split(";")[0])],
        )
    ]
    result = await provider.generate(
        messages,
        model=default_model(provider_name),
        temperature=0.1,
        max_tokens=4096,
        json_mode=True,
    )
    return _parse_answers_json(result.text), result
