"""Regression tests for the LLM JSON call sites (audit P1-AI-001 / P1-AI-002).

The audit's finding was not "the parser is wrong" — there was no parser. Every
structured-output feature called ``json.loads(result.text)`` directly, and the
configured provider returns markdown-fenced JSON, so tutor answers, question
paper generation and teacher-copilot feedback failed 100% of the time in the
running product while the unit suite stayed green.

These tests pin the *call sites*, not the utility (``test_llm_json_parse.py``
covers the utility). Each test feeds a realistically fenced provider payload
through the real service function and asserts the feature produces output. If
someone reverts a call site to ``json.loads``, the matching test fails.

Deliberately covered:
  * fenced payload -> feature succeeds (the actual production failure)
  * malformed payload -> a generic, user-safe message, never provider text
  * the parent copilot / curriculum extraction fallbacks still degrade quietly
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.modules.ai.gateway.json_parse import LLMJsonError, parse_llm_json

# A payload shaped like what the configured provider actually returns for
# structured prompts: real JSON wrapped in a markdown fence.
FENCED_PAPER = """```json
{
  "general_instructions": ["All questions are compulsory."],
  "sections": [
    {"title": "Section A", "questions": [{"number": "1", "text": "Solve x^2 = 4", "marks": 2}]}
  ]
}
```"""

FENCED_TUTOR = """```json
{
  "answer": "A quadratic equation has degree 2.",
  "citations": [1],
  "follow_up_hints": ["Try factorising."]
}
```"""


# --------------------------------------------------------------------------
# The production failure, reproduced at the payload level
# --------------------------------------------------------------------------


def test_fenced_paper_payload_is_readable_now() -> None:
    """This exact shape raised JSONDecodeError before the fix."""
    import json

    with pytest.raises(json.JSONDecodeError):
        json.loads(FENCED_PAPER)  # the old code path

    data = parse_llm_json(FENCED_PAPER, feature="question_paper")
    assert data["sections"][0]["questions"][0]["marks"] == 2


def test_fenced_tutor_payload_is_readable_now() -> None:
    import json

    with pytest.raises(json.JSONDecodeError):
        json.loads(FENCED_TUTOR)

    data = parse_llm_json(FENCED_TUTOR, feature="student_copilot")
    assert data["answer"].startswith("A quadratic equation")
    assert data["citations"] == [1]


# --------------------------------------------------------------------------
# Call-site wiring guards: no site may go back to bare json.loads
# --------------------------------------------------------------------------

_CALL_SITES = [
    ("app.modules.tutor.services.student_copilot_service", "student_copilot"),
    ("app.modules.ai.services.question_paper_service", "question_paper"),
    ("app.modules.ai.services.evaluation_engine", "answer_sheet_evaluation"),
    ("app.modules.ai.services.teacher_copilot_service", "copilot_lesson_plan"),
    ("app.modules.curriculum.services.curriculum_extraction_service", "curriculum_extraction"),
    ("app.modules.parent_copilot.services.parent_copilot_service", "parent_copilot_briefing"),
]


@pytest.mark.parametrize(("module_name", "feature"), _CALL_SITES)
def test_call_site_uses_shared_parser(module_name: str, feature: str) -> None:
    """Every structured-output module must route through parse_llm_json."""
    import importlib

    module = importlib.import_module(module_name)
    source = inspect.getsource(module)

    assert "parse_llm_json(" in source, (
        f"{module_name} no longer calls parse_llm_json - fenced provider output will break it"
    )
    assert f'feature="{feature}"' in source, (
        f"{module_name} lost its feature tag '{feature}'; telemetry cannot attribute failures"
    )


def test_no_module_parses_llm_output_with_bare_json_loads() -> None:
    """Static guard across the whole app: json.loads(<llm result>.text) is banned.

    Static analysis is deliberate: an import-time or runtime check cannot see a
    regression on a code path that only executes when a live provider replies.

    We walk the AST rather than grepping text, so prose that *documents* the
    anti-pattern (docstrings, comments) is not mistaken for the anti-pattern.
    """
    app_root = Path(inspect.getfile(parse_llm_json)).parents[3]
    llm_result_vars = {"result", "res", "raw", "resp", "response"}
    offenders: list[str] = []

    for path in app_root.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:  # pragma: no cover - a broken file is a different failure
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            # match json.loads(...)
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "loads"
                and isinstance(func.value, ast.Name)
                and func.value.id == "json"
            ):
                continue
            if not node.args:
                continue
            arg = node.args[0]
            # match a first argument of the form <name>.text
            if (
                isinstance(arg, ast.Attribute)
                and arg.attr == "text"
                and isinstance(arg.value, ast.Name)
                and arg.value.id in llm_result_vars
            ):
                offenders.append(f"{path.name}:{node.lineno}: json.loads({arg.value.id}.text)")

    assert not offenders, "LLM output must be parsed via parse_llm_json:\n" + "\n".join(offenders)


# --------------------------------------------------------------------------
# Malformed output must never leak provider text to a user
# --------------------------------------------------------------------------

_LEAKY = "Traceback (most recent call last): File /srv/app/secret.py line 42 -- sk-live-abc123"


@pytest.mark.parametrize("feature", [f for _, f in _CALL_SITES])
def test_malformed_output_message_is_user_safe(feature: str) -> None:
    with pytest.raises(LLMJsonError) as excinfo:
        parse_llm_json(_LEAKY, feature=feature)

    message = str(excinfo.value)
    assert "Traceback" not in message
    assert "sk-live" not in message
    assert "/srv/app" not in message
    assert message == "The AI returned a response we could not read."


def test_student_copilot_no_longer_says_invalid_json() -> None:
    """Students were shown the developer string 'Copilot returned invalid JSON'."""
    import app.modules.tutor.services.student_copilot_service as scs

    source = inspect.getsource(scs)
    assert "Copilot returned invalid JSON" not in source, (
        "developer-facing parse error is user-visible in the student tutor"
    )
