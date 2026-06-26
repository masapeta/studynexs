"""Production hardening for the LLM gateway."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.modules.ai.gateway.errors import raise_http_for_llm_error


def test_value_error_maps_to_400():
    with pytest.raises(HTTPException) as exc:
        raise_http_for_llm_error(ValueError("bad input"), log_event="test")
    assert exc.value.status_code == 400
    assert exc.value.detail == "bad input"


def test_runtime_error_maps_to_503():
    with pytest.raises(HTTPException) as exc:
        raise_http_for_llm_error(RuntimeError("OPENAI_API_KEY is not configured"), log_event="test")
    assert exc.value.status_code == 503


def test_timeout_maps_to_504():
    with pytest.raises(HTTPException) as exc:
        raise_http_for_llm_error(TimeoutError("slow"), log_event="test")
    assert exc.value.status_code == 504


def test_generic_error_maps_to_503():
    with pytest.raises(HTTPException) as exc:
        raise_http_for_llm_error(Exception("provider blew up"), log_event="test")
    assert exc.value.status_code == 503
    assert "failed" in exc.value.detail.lower()
