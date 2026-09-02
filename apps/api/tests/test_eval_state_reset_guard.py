"""Regression guard for stale evaluation state carryover in the web UI.

The trust bug was a "New evaluation" action that only cleared `activeEval`, leaving
student, file, and typed answers from the previous student in memory.
"""
from __future__ import annotations

import re
from pathlib import Path

EVALUATE_PAGE = (
    Path(__file__).resolve().parents[3]
    / "apps"
    / "admin-web"
    / "src"
    / "app"
    / "dashboard"
    / "teaching"
    / "exams"
    / "[examId]"
    / "evaluate"
    / "page.tsx"
)


def _function_body(source: str, name: str) -> str:
    pattern = re.compile(rf"function {re.escape(name)}\(.*?\) \{{(?P<body>.*?)\n  \}}", re.DOTALL)
    match = pattern.search(source)
    assert match is not None, f"{name}() not found in evaluate page"
    return match.group("body")


def test_new_evaluation_action_resets_all_mutable_input_state() -> None:
    source = EVALUATE_PAGE.read_text(encoding="utf-8")

    assert "onClick={() => setActiveEval(null)}" not in source
    assert "onClick={startNewEvaluation}" in source

    reset_body = _function_body(source, "startNewEvaluation")
    required_resets = (
        "setActiveEval(null);",
        "setSelectedStudent(\"\");",
        "setSheetFile(null);",
        "setAnswers(buildInitialAnswers(questions));",
        "setOverrides({});",
        "setOverrideReasons({});",
        "setManualReviewAcknowledgements({});",
    )
    for expected in required_resets:
        assert expected in reset_body

    load_body = _function_body(source, "loadEval")
    assert "setSheetFile(null);" in load_body
    assert "setAnswers(buildInitialAnswers(questions));" in load_body
