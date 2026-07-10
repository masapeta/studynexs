"""Sanitize LLM outputs and structured AI artifacts before persistence or display."""
from __future__ import annotations

import re

from app.modules.ai.gateway.input_guard import (
    _CONTROL_CHARS,
    _SENSITIVE_RUNTIME,
    sanitize_answer_map,
    sanitize_prompt_text,
)

_SECRET_PATTERNS = re.compile(
    r"(sk-[a-zA-Z0-9]{20,}|"
    r"AIza[a-zA-Z0-9_-]{20,}|"
    r"Bearer\s+[a-zA-Z0-9._-]{20,})"
)

_MAX_NARRATIVE_LEN = 4000
_MAX_REMARK_LEN = 4000
_MAX_SECTIONS = 24
_MAX_QUESTIONS_PER_SECTION = 60
_MAX_OPTIONS = 6
_MAX_CONCEPTS_PER_Q = 12
_MAX_CITATIONS_PER_Q = 24


def _apply_question_metadata(src: dict, item: dict) -> None:
    """Carry optional Assessment-Intelligence metadata onto a sanitized question.

    Bloom level, difficulty, learning outcome, concept tags, and citation indices are only
    added when present, so ungrounded/free-text questions stay unchanged. Citations are the
    1-based indices into the paper's ``grounding_sources`` — coerced to positive ints so the
    trace can never carry arbitrary strings.
    """
    bloom = sanitize_prompt_text(
        src.get("bloom"), max_length=40, field_name="bloom", reject_injection=False
    )
    if bloom:
        item["bloom"] = bloom

    difficulty = sanitize_prompt_text(
        src.get("difficulty"), max_length=24, field_name="difficulty", reject_injection=False
    )
    if difficulty:
        item["difficulty"] = difficulty.lower()

    learning_outcome = sanitize_prompt_text(
        src.get("learning_outcome"),
        max_length=500,
        field_name="learning outcome",
        reject_injection=False,
    )
    if learning_outcome:
        item["learning_outcome"] = learning_outcome

    concepts = src.get("concepts")
    if isinstance(concepts, list):
        cleaned = [
            sanitize_prompt_text(
                str(c), max_length=120, field_name="concept", reject_injection=False
            )
            for c in concepts[:_MAX_CONCEPTS_PER_Q]
        ]
        cleaned = [c for c in cleaned if c]
        if cleaned:
            item["concepts"] = cleaned

    citations = src.get("citations")
    if isinstance(citations, list):
        idxs: list[int] = []
        for c in citations[:_MAX_CITATIONS_PER_Q]:
            try:
                n = int(c)
            except (TypeError, ValueError):
                continue
            if n >= 1:
                idxs.append(n)
        if idxs:
            item["citations"] = idxs


def sanitize_llm_plain_text(
    text: str | None,
    *,
    max_length: int = _MAX_NARRATIVE_LEN,
    field_name: str = "text",
) -> str:
    """Strip control chars, bound length, and redact secret-like substrings from model text."""
    if text is None:
        return ""
    cleaned = _CONTROL_CHARS.sub("", str(text).strip())
    if not cleaned:
        return ""
    cleaned = _SECRET_PATTERNS.sub("[redacted]", cleaned)
    if _SENSITIVE_RUNTIME.search(cleaned):
        cleaned = "AI draft unavailable — please edit manually."
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
    return cleaned


def sanitize_paper_sections(raw_sections: object) -> list[dict]:
    """Validate teacher/LLM paper sections before save — bounds + injection checks."""
    if raw_sections is None:
        return []
    if not isinstance(raw_sections, list):
        raise ValueError("sections must be a list")
    if len(raw_sections) > _MAX_SECTIONS:
        raise ValueError(f"At most {_MAX_SECTIONS} sections allowed")

    out: list[dict] = []
    for raw in raw_sections:
        if not isinstance(raw, dict):
            raise ValueError("Each section must be an object")
        title = sanitize_prompt_text(
            str(raw.get("title", "")),
            max_length=200,
            field_name="section title",
        ) or "Section"
        instructions = sanitize_prompt_text(
            raw.get("instructions"),
            max_length=2000,
            field_name="section instructions",
        )
        questions_in = raw.get("questions") or []
        if not isinstance(questions_in, list):
            raise ValueError("section questions must be a list")
        if len(questions_in) > _MAX_QUESTIONS_PER_SECTION:
            raise ValueError(f"At most {_MAX_QUESTIONS_PER_SECTION} questions per section")

        questions: list[dict] = []
        for q in questions_in:
            if not isinstance(q, dict):
                raise ValueError("Each question must be an object")
            qtext = sanitize_prompt_text(
                str(q.get("text", "")),
                max_length=4000,
                field_name="question text",
            ) or ""
            marks = float(q.get("marks", 0) or 0)
            if marks < 0 or marks > 100:
                raise ValueError("Question marks must be between 0 and 100")
            qtype = sanitize_prompt_text(
                str(q.get("type", "short")),
                max_length=32,
                field_name="question type",
                reject_injection=False,
            ) or "short"
            number = sanitize_prompt_text(
                str(q.get("number", "")),
                max_length=16,
                field_name="question number",
                reject_injection=False,
            ) or ""
            item: dict = {
                "number": number,
                "text": qtext,
                "marks": marks,
                "type": qtype,
            }
            options = q.get("options")
            if options is not None:
                if not isinstance(options, list):
                    raise ValueError("options must be a list")
                if len(options) > _MAX_OPTIONS:
                    raise ValueError(f"At most {_MAX_OPTIONS} options per question")
                item["options"] = [
                    sanitize_prompt_text(str(o), max_length=500, field_name="option") or ""
                    for o in options
                ]
            if q.get("answer_key") is not None:
                item["answer_key"] = sanitize_prompt_text(
                    str(q.get("answer_key")),
                    max_length=4000,
                    field_name="answer key",
                ) or ""
            _apply_question_metadata(q, item)
            questions.append(item)

        out.append({
            "title": title,
            "instructions": instructions,
            "questions": questions,
        })
    return out


def sanitize_vision_answers(raw: dict[str, str] | None) -> dict[str, str]:
    """Bound OCR/transcription answers from vision models."""
    return sanitize_answer_map(raw)
