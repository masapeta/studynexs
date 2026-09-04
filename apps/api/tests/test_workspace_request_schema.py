"""Regression tests for Phase 0 workspace request validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.workspace.schemas.request import WorkspaceTurnRequest


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "read", "text": None},
        {"mode": "read", "text": {"x": 1}},
        {"mode": "read", "text": ["hello"]},
    ],
)
def test_workspace_turn_request_rejects_non_string_text(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="valid string"):
        WorkspaceTurnRequest.model_validate(payload)


def test_workspace_turn_request_sanitizes_valid_string_text() -> None:
    request = WorkspaceTurnRequest.model_validate({"mode": "read", "text": "  show Aarav  "})

    assert request.text == "show Aarav"


def test_workspace_turn_request_rejects_blank_text_after_sanitization() -> None:
    with pytest.raises(ValidationError, match="text is required"):
        WorkspaceTurnRequest.model_validate({"mode": "read", "text": "   "})
