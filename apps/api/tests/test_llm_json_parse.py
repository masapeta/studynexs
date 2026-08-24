"""Unit tests for parse_llm_json (audit P1-AI-001/002).

The first case is the exact byte-shape captured from the configured provider (ollama
gemma4:cloud) while reproducing the audit finding — nine call sites used bare
json.loads(result.text) and failed on it 100% of the time.
"""

from __future__ import annotations

import pytest

from app.modules.ai.gateway.json_parse import LLMJsonError, parse_llm_json

# Verbatim from the live reproduction (tmp/qa-audit/p2_shapes.py).
_REAL_FENCED = (
    '```json\n{\n "answer": "A quadratic equation is a second-degree polynomial.",\n'
    ' "citations": [\n  1\n ],\n "follow_up_hints": [\n  "What if a is zero?"\n ]\n}\n```'
)


def test_real_provider_fenced_payload_is_recovered():
    """The exact failure that broke the Tutor for every question."""
    out = parse_llm_json(_REAL_FENCED, feature="test")
    assert out["answer"].startswith("A quadratic equation")
    assert out["citations"] == [1]
    assert out["follow_up_hints"] == ["What if a is zero?"]


def test_bare_json_still_works():
    assert parse_llm_json('{"ok": true}', feature="test") == {"ok": True}


@pytest.mark.parametrize(
    "raw",
    [
        '   {"a": 1}   ',
        '\n\n{"a": 1}\n\n',
        '\t{"a": 1}\t',
    ],
)
def test_surrounding_whitespace(raw):
    assert parse_llm_json(raw, feature="test") == {"a": 1}


@pytest.mark.parametrize(
    "raw",
    [
        '```json\n{"a": 1}\n```',
        '```JSON\n{"a": 1}\n```',
        '```\n{"a": 1}\n```',
        '```json\r\n{"a": 1}\r\n```',
        '  ```json\n{"a": 1}\n```  ',
        '```json\n{"a": 1}```',
    ],
)
def test_fence_variants(raw):
    assert parse_llm_json(raw, feature="test") == {"a": 1}


def test_json_embedded_in_prose():
    raw = 'Sure! Here is the paper you asked for:\n{"sections": []}\nHope that helps.'
    assert parse_llm_json(raw, feature="test") == {"sections": []}


def test_braces_inside_string_values_do_not_break_slicing():
    """Generated question text legitimately contains braces — a rfind('}') slice would break."""
    raw = 'Here you go: {"text": "solve {x} for }", "marks": 2} — done'
    out = parse_llm_json(raw, feature="test")
    assert out["text"] == "solve {x} for }"
    assert out["marks"] == 2


def test_nested_structures_survive():
    raw = '```json\n{"sections":[{"questions":[{"text":"a","marks":1}]}]}\n```'
    out = parse_llm_json(raw, feature="test")
    assert out["sections"][0]["questions"][0]["marks"] == 1


def test_list_top_level_when_expected():
    assert parse_llm_json('```json\n[1, 2, 3]\n```', feature="test", expect=list) == [1, 2, 3]


def test_wrong_container_is_rejected():
    """A model returning [] where the caller needs {} must fail here, not deeper."""
    with pytest.raises(LLMJsonError):
        parse_llm_json('[1, 2]', feature="test", expect=dict)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "   ",
        "\n\t ",
    ],
)
def test_empty_response_fails_safely(raw):
    with pytest.raises(LLMJsonError):
        parse_llm_json(raw, feature="test")


@pytest.mark.parametrize(
    "raw",
    [
        "I cannot help with that request.",
        "```json\n{ not json at all\n```",
        '{"unterminated": ',
        "{'single': 'quotes'}",
        "<html><body>502 Bad Gateway</body></html>",
    ],
)
def test_malformed_output_fails_safely(raw):
    with pytest.raises(LLMJsonError):
        parse_llm_json(raw, feature="test")


def test_malformed_error_message_does_not_leak_model_output():
    """The user-facing string must never carry provider text (audit Phase 6)."""
    secret = "sk-live-abcdef1234567890 internal trace /app/modules/ai"
    with pytest.raises(LLMJsonError) as ei:
        parse_llm_json(f"garbage {secret}", feature="test")
    msg = str(ei.value)
    assert secret not in msg
    assert "sk-live" not in msg
    assert "/app/" not in msg


def test_truncated_json_is_not_silently_repaired():
    """Half a paper must fail loudly — a silently 'fixed' paper is worse than an error."""
    with pytest.raises(LLMJsonError):
        parse_llm_json('{"sections": [{"questions": [{"text": "Q1", "marks":', feature="test")
