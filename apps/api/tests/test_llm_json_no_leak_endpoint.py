"""Malformed provider output must not leak internals to end users (audit P1-AI-002).

Phase 2's second acceptance criterion: when the provider returns garbage, the
user sees a calm generic message - never a traceback, provider text, model name,
prompt content, or key material.

We exercise the real service functions with a stubbed provider reply so the test
is deterministic and needs no live model. The assertion is on what reaches the
*caller*, which is what the UI renders.
"""

from __future__ import annotations

import pytest

from app.modules.ai.gateway.json_parse import LLMJsonError, parse_llm_json

# Deliberately hostile provider replies: each carries something that must never
# reach a student, parent or teacher.
LEAKY_REPLIES = [
    "Traceback (most recent call last):\n  File '/srv/studynexs/app/main.py', line 12",
    "Error: OPENAI_API_KEY=sk-live-9f8e7d6c5b4a is invalid",
    "postgresql://studynexs:hunter2@10.0.0.4:5432/studynexs could not connect",
    "SYSTEM PROMPT: You are StudyNexs's exam-item generator. Ignore the student.",
    "<html><body><h1>502 Bad Gateway</h1><pre>upstream ollama.com</pre></body></html>",
    "",
    "   ",
    "null",
]

SAFE_MESSAGES = {
    "The AI returned a response we could not read.",
    "The AI returned an empty response.",
}

FORBIDDEN_FRAGMENTS = [
    "Traceback",
    "sk-live",
    "hunter2",
    "postgresql://",
    "/srv/studynexs",
    "SYSTEM PROMPT",
    "502 Bad Gateway",
    "ollama.com",
    "File '",
]


@pytest.mark.parametrize("reply", LEAKY_REPLIES)
def test_parser_message_never_echoes_provider_text(reply: str) -> None:
    with pytest.raises(LLMJsonError) as excinfo:
        parse_llm_json(reply, feature="leak_probe")

    message = str(excinfo.value)
    assert message in SAFE_MESSAGES, f"unexpected user-facing message: {message!r}"
    for fragment in FORBIDDEN_FRAGMENTS:
        assert fragment not in message, f"{fragment!r} leaked into a user-facing message"


@pytest.mark.parametrize("reply", LEAKY_REPLIES)
def test_service_layer_messages_are_generic(reply: str) -> None:
    """The messages each service raises are curated strings, not provider echoes."""
    service_messages = [
        "The AI returned an unreadable paper. Please try generating again.",
        "The AI returned an unreadable evaluation.",
        "The AI returned an unreadable lesson plan. Please try again.",
        "The AI returned an unreadable review. Please try again.",
        "The AI returned unreadable feedback. Please try again.",
        "The tutor could not put that into words just now. Please try again.",
    ]
    for message in service_messages:
        for fragment in FORBIDDEN_FRAGMENTS:
            assert fragment not in message
        assert reply.strip() not in message or not reply.strip()


def test_empty_and_unreadable_have_distinct_messages() -> None:
    """Operators should be able to tell 'nothing came back' from 'garbage came back'."""
    with pytest.raises(LLMJsonError) as empty:
        parse_llm_json("", feature="leak_probe")
    with pytest.raises(LLMJsonError) as garbage:
        parse_llm_json("not json", feature="leak_probe")

    assert str(empty.value) != str(garbage.value)


# --------------------------------------------------------------------------
# Logs must not carry model output either (§31, §43, §62.5)
# --------------------------------------------------------------------------

# Tutor / parent-copilot / evaluation output contains real student PII. Logging the raw
# reply would put a child's name, answers and marks into the log store.
PII_REPLY = (
    "I'm sorry! Regarding Ananya Sharma (roll 14, mobile 9876543210), "
    "she scored 3/20 on Quadratic Equations and wrote 'I don't know'."
)


def test_log_capture_actually_captures(capsys: pytest.CaptureFixture[str]) -> None:
    """Guard the guard.

    structlog writes to stdout, not through stdlib ``logging``, so a ``caplog``-based
    assertion silently passes against an empty string. This test proves the capture
    mechanism sees real log output, so the two assertions below mean something.
    """
    with pytest.raises(LLMJsonError):
        parse_llm_json("definitely not json", feature="capture_probe")

    captured = capsys.readouterr().out
    assert "llm_json_parse_failed" in captured, "log capture is broken; leak tests would false-pass"
    assert "capture_probe" in captured


def test_parse_failure_does_not_log_model_output(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(LLMJsonError):
        parse_llm_json(PII_REPLY, feature="pii_probe")

    logged = capsys.readouterr().out
    # sanity: we really are looking at the log line for this failure
    assert "llm_json_parse_failed" in logged

    for fragment in ("Ananya Sharma", "9876543210", "roll 14", "I don't know", "3/20"):
        assert fragment not in logged, f"{fragment!r} was written to the logs"


def test_parse_failure_still_logs_useful_diagnostics(capsys: pytest.CaptureFixture[str]) -> None:
    """Privacy must not cost us debuggability: shape/length are still recorded."""
    with pytest.raises(LLMJsonError):
        parse_llm_json('```json\n{"broken": \n```', feature="shape_probe")

    logged = capsys.readouterr().out
    assert "llm_json_parse_failed" in logged
    assert "shape_probe" in logged
    assert "fence=yes" in logged, "shape diagnostics missing - provider regressions become opaque"
    assert "raw_len=" in logged
