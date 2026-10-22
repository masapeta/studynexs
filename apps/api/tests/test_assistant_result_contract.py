"""Phase 9: the typed result-block contract for the agentic assistant.

Asserts the contract is REAL (strict validation catches malformed known payloads so schema drift
can't go invisible) and COMPATIBLE (validation returns the wire dict unchanged; unknown kinds and
production-mode malformed payloads never break a turn). Representative payloads mirror the actual
producers in capabilities/service/executor.
"""

from __future__ import annotations

import json

import pytest

from app.modules.workspace.assistant.result import (
    RESULT_KINDS,
    validate_block,
)

# One representative payload per known kind — fields copied from the real producers.
_SAMPLES: dict[str, dict] = {
    "metrics": {
        "kind": "metrics", "title": "Attendance — Ravi", "subtitle": "8A",
        "source": "Attendance System",
        "metrics": [{"label": "Attendance", "value": 82, "format": "percent"},
                    {"label": "Present", "value": 41}],
        "href": "/dashboard/attendance", "href_label": "Open attendance",
    },
    "table": {
        "kind": "table", "title": "Students in 8A", "source": "Student Information System",
        "columns": [{"key": "admission_no", "label": "Admission no"},
                    {"key": "name", "label": "Student"}],
        "rows": [{"admission_no": "ADM1", "name": "Ravi"}],
        "empty_message": "No students yet.", "href": "/dashboard/students",
        "href_label": "Open students",
    },
    "guide": {
        "kind": "guide", "title": "Here's where to look", "message": "Try these.",
        "suggestions": [{"label": "Students", "href": "/dashboard/students"}],
    },
    "error": {"kind": "error", "title": "Couldn't complete that", "message": "Try again."},
    "clarify": {
        "kind": "clarify", "title": "Which class?", "message": "Name it.",
        "options": [{"id": "8a", "label": "8A"}],
    },
    "not_found": {"kind": "not_found", "title": "No student found", "message": "Check the ID."},
    "document": {
        "kind": "document", "title": "From school policy", "message": "Policy text.",
        "citations": [{"title": "Handbook", "document_type": "policy", "snippet": "..."}],
    },
    "navigate": {"kind": "navigate", "title": "Opening", "href": "/dashboard", "label": "Dashboard"},
    "mixed": {
        "kind": "mixed", "title": "Result",
        "data": {"kind": "metrics", "title": "t", "metrics": []},
        "document": {"kind": "document", "title": "policy", "message": "x", "citations": []},
    },
    "workflow": {
        "kind": "workflow", "workflow_id": "question_paper",
        "title": "Question Paper — 8A Science", "workflow_state": "waiting_for_approval",
        "paper_status": "draft",
        "summary": {"paper_id": "x", "class": "8A", "subject": "Science"},
        "actions": [{"label": "Review", "href": "/dashboard/question-papers/x"}],
        "message": "Drafted.",
    },
    "action_preview": {
        "kind": "action_preview", "action": "publish_notice",
        "title": "Review notice before publishing", "status": "waiting_for_confirmation",
        "preview": {"title": "Holiday", "content": "Tomorrow", "audience": "external"},
        "confirm_action": {"label": "Publish Notice", "endpoint": "/api/v1/x", "payload": {}},
        "message": "Confirm to publish.",
    },
}


def test_every_known_kind_has_a_sample():
    assert set(_SAMPLES) == set(RESULT_KINDS), "sample coverage must match RESULT_KINDS exactly"


@pytest.mark.parametrize("kind", sorted(RESULT_KINDS))
def test_known_kind_validates_strict(kind):
    block = _SAMPLES[kind]
    out = validate_block(block, strict=True)
    assert out is block  # returns the original object, never a reshaped dump


@pytest.mark.parametrize("kind", sorted(RESULT_KINDS))
def test_wire_representation_preserved(kind):
    block = _SAMPLES[kind]
    before = json.dumps(block, sort_keys=True)
    out = validate_block(block)
    assert json.dumps(out, sort_keys=True) == before  # byte-for-byte identical


def test_extra_fields_are_preserved():
    block = {"kind": "metrics", "title": "t", "metrics": [], "x_custom": {"a": 1}}
    out = validate_block(block, strict=True)
    assert out["x_custom"] == {"a": 1}


# ── Compatibility: never break a turn ──────────────────────────────────────────


def test_unknown_kind_passes_through_without_raising():
    block = {"kind": "some_future_kind", "title": "t", "whatever": 1}
    out = validate_block(block, strict=True)  # even strict must not raise on an UNKNOWN kind
    assert out is block


def test_missing_kind_passes_through():
    block = {"title": "no kind here"}
    out = validate_block(block)
    assert out is block


def test_malformed_known_kind_raises_in_strict_mode():
    # metrics with a wrong-typed field — drift must be caught in CI.
    bad = {"kind": "metrics", "metrics": "not-a-list"}
    with pytest.raises(Exception):
        validate_block(bad, strict=True)


def test_malformed_known_kind_is_tolerated_in_production_mode():
    bad = {"kind": "metrics", "metrics": "not-a-list"}
    out = validate_block(bad)  # strict=False -> logged, not raised
    assert out is bad


def test_navigate_requires_href_in_strict_mode():
    with pytest.raises(Exception):
        validate_block({"kind": "navigate", "title": "Opening"}, strict=True)


def test_workflow_requires_workflow_id_in_strict_mode():
    with pytest.raises(Exception):
        validate_block({"kind": "workflow", "title": "x"}, strict=True)
