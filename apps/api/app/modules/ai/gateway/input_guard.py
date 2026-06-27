"""Sanitize untrusted text before LLM prompts and bound user-controlled AI inputs."""
from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?(previous|prior|above)\s+instructions?"
    r"|disregard\s+(the\s+)?(system|above)"
    r"|you\s+are\s+now"
    r"|<\s*/?\s*system\s*>"
    r"|```\s*system)",
    re.IGNORECASE,
)

ALLOWED_DIFFICULTIES = frozenset({"easy", "balanced", "hard"})

_SENSITIVE_RUNTIME = re.compile(
    r"(api[_-]?key|secret|token|password|not configured)",
    re.IGNORECASE,
)


def sanitize_prompt_text(
    text: str | None,
    *,
    max_length: int = 500,
    field_name: str = "text",
    reject_injection: bool = True,
) -> str | None:
    """Strip control chars, enforce length, optionally block prompt-injection phrases."""
    if text is None:
        return None
    cleaned = _CONTROL_CHARS.sub("", str(text).strip())
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")
    if reject_injection and _INJECTION_PATTERNS.search(cleaned):
        raise ValueError(f"{field_name} contains disallowed content")
    return cleaned


def sanitize_topic_list(
    topics: list[str] | None,
    *,
    max_topics: int = 20,
    max_topic_len: int = 120,
) -> list[str]:
    if not topics:
        return []
    if len(topics) > max_topics:
        raise ValueError(f"At most {max_topics} topics allowed")
    out: list[str] = []
    for raw in topics:
        t = sanitize_prompt_text(raw, max_length=max_topic_len, field_name="topic")
        if t:
            out.append(t)
    return out


def sanitize_answer_map(
    answers: dict[str, str] | None,
    *,
    max_keys: int = 100,
    max_key_len: int = 16,
    max_value_len: int = 2000,
) -> dict[str, str]:
    if not answers:
        return {}
    if len(answers) > max_keys:
        raise ValueError(f"At most {max_keys} answers allowed")
    out: dict[str, str] = {}
    for key, val in answers.items():
        k = (key or "").strip()
        if not k or len(k) > max_key_len:
            raise ValueError("Invalid question number key")
        v = sanitize_prompt_text(
            val or "",
            max_length=max_value_len,
            field_name="answer",
            reject_injection=False,
        ) or ""
        out[k] = v
    return out


def sanitize_lesson_key(key: str) -> str:
    k = (key or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", k):
        raise ValueError("Invalid lesson key")
    return k


def safe_provider_error_detail(exc: BaseException) -> str:
    """Never expose API keys or provider config in HTTP responses."""
    msg = str(exc)
    if _SENSITIVE_RUNTIME.search(msg):
        return "AI service is temporarily unavailable. Please try again later."
    if len(msg) > 120:
        return "AI service is temporarily unavailable. Please try again later."
    return msg
