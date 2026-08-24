"""Tolerant JSON parsing for LLM output (audit P1-AI-001/002).

Models asked for JSON routinely wrap it in a Markdown fence, so nine call sites doing bare
``json.loads(result.text)`` failed 100% of the time against the configured provider — breaking
the Student Tutor, question-paper generation and Teacher Copilot. Observed shapes:

    '```json\\n{\\n  "answer": "..."\\n}\\n```'   <- fenced (structured prompts)
    '{"ok": true}'                               <- bare (trivial prompts)

Every LLM JSON parse goes through :func:`parse_llm_json`. It is deliberately narrow: it
recovers *well-formed JSON inside decoration*, and never repairs malformed JSON — a silently
"fixed" exam paper or grade is worse than a clean failure.
"""

from __future__ import annotations

import json
import re
from typing import Any

import structlog

logger = structlog.get_logger()

# ```json ... ``` / ``` ... ``` — any language tag, optional trailing newline before the close.
_FENCE = re.compile(
    r"^\s*```[ \t]*[A-Za-z0-9_+-]*[ \t]*\r?\n(?P<body>.*?)\r?\n?[ \t]*```\s*$",
    re.DOTALL,
)


class LLMJsonError(ValueError):
    """Model output could not be parsed as JSON.

    Callers translate this into their own user-facing message. The raw text is never returned
    to a user *and never logged* — only its structural shape is (see :func:`_shape`), because
    model output can contain student PII and prompt context.
    """


def _strip_fence(text: str) -> str:
    m = _FENCE.match(text)
    return m.group("body") if m else text


def _shape(text: str) -> str:
    """Describe unparseable output without logging its content.

    Model output for the tutor, parent copilot and evaluation carries student PII (names,
    answers, marks) and can echo prompt context, so the raw text must never reach the logs
    (§31, §43, §62.5). This records only structural facts — enough to recognise a provider
    regression (fence markers? refusal prose? truncated JSON?) with nothing sensitive in it.
    """
    head = text.lstrip()[:1] or "?"
    tail = text.rstrip()[-1:] or "?"
    return (
        f"starts={head!r} ends={tail!r} "
        f"fence={'yes' if '```' in text else 'no'} "
        f"braces={text.count('{')}/{text.count('}')} "
        f"brackets={text.count('[')}/{text.count(']')}"
    )


def _slice_outermost(text: str, open_ch: str, close_ch: str) -> str | None:
    """Return the outermost balanced open_ch..close_ch span, ignoring string literals.

    A naive ``find('{')`` + ``rfind('}')`` would mis-slice when braces appear inside string
    values, which is common in generated question text.
    """
    start = text.find(open_ch)
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_llm_json(
    raw: str | None,
    *,
    feature: str,
    expect: type[dict] | type[list] = dict,
) -> Any:
    """Parse model output that is *supposed* to be JSON.

    Handles, in order: exact JSON, surrounding whitespace, a Markdown code fence, and prose
    wrapped around a single JSON value ("Here is the paper: {...}"). Raises
    :class:`LLMJsonError` on anything else.

    Args:
        raw: the model's text (``LLMResult.text``); ``None``/empty is an error.
        feature: log tag identifying the call site.
        expect: ``dict`` (default) or ``list`` — the top-level type the caller needs, so a
            model returning the wrong container fails here instead of deeper in the caller.
    """
    if raw is None or not str(raw).strip():
        logger.error("llm_json_empty", feature=feature)
        raise LLMJsonError("The AI returned an empty response.")

    text = str(raw).strip()
    open_ch, close_ch = ("[", "]") if expect is list else ("{", "}")

    candidates = [text]
    unfenced = _strip_fence(text).strip()
    if unfenced != text:
        candidates.append(unfenced)
    # Last resort: pull the JSON value out of surrounding prose.
    sliced = _slice_outermost(unfenced, open_ch, close_ch)
    if sliced and sliced not in candidates:
        candidates.append(sliced)

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            last_error = exc
            continue
        if not isinstance(parsed, expect):
            last_error = TypeError(
                f"expected top-level {expect.__name__}, got {type(parsed).__name__}"
            )
            continue
        if candidate is not text:
            logger.info("llm_json_recovered", feature=feature, strategy="fence_or_slice")
        return parsed

    logger.error(
        "llm_json_parse_failed",
        feature=feature,
        error=str(last_error)[:200],
        raw_len=len(text),
        raw_shape=_shape(text),
    )
    raise LLMJsonError("The AI returned a response we could not read.")
