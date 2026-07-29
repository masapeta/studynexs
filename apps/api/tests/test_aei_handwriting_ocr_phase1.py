"""AEI Handwriting OCR Phase 1 - Gemini Flash transcription gate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.modules.ai.gateway.base import LLMResult
from app.modules.examinations.services import answer_sheet_vision as vision


def test_handwriting_ocr_phase1_flag_defaults_disabled():
    assert Settings.model_fields["AEI_HANDWRITING_OCR_PHASE1_ENABLED"].default is False


def test_vision_llm_unavailable_when_phase1_flag_disabled(monkeypatch):
    monkeypatch.setattr(vision.settings, "AEI_HANDWRITING_OCR_PHASE1_ENABLED", False)
    monkeypatch.setattr(vision.settings, "AI_VISION_PRIMARY_PROVIDER", "")
    monkeypatch.setattr(vision.settings, "GEMINI_API_KEY", "configured")

    assert vision.vision_llm_available() is False


@pytest.mark.asyncio
async def test_phase1_flag_off_does_not_invoke_gateway(monkeypatch):
    monkeypatch.setattr(vision.settings, "AEI_HANDWRITING_OCR_PHASE1_ENABLED", False)
    monkeypatch.setattr(vision.settings, "GEMINI_API_KEY", "configured")

    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("gateway should not be invoked when Phase 1 is disabled")

    monkeypatch.setattr(vision, "generate_llm", fail_if_called)

    answers, result = await vision.extract_answers_from_image(
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
        question_schema=[{"no": 1, "max_marks": 2}],
        rubrics={"1": {"question_text": "Define force"}},
    )

    assert answers == {}
    assert result is None


@pytest.mark.asyncio
async def test_phase1_flag_on_invokes_gateway_with_gemini_model(monkeypatch):
    monkeypatch.setattr(vision.settings, "AEI_HANDWRITING_OCR_PHASE1_ENABLED", True)
    monkeypatch.setattr(vision.settings, "AI_VISION_PRIMARY_PROVIDER", "gemini")
    monkeypatch.setattr(vision.settings, "AI_VISION_PRIMARY_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(vision.settings, "AI_VISION_FALLBACK_PROVIDER", "")
    monkeypatch.setattr(vision.settings, "GEMINI_API_KEY", "configured")

    calls: list[dict] = []

    async def fake_generate_llm(*_args, **kwargs):
        calls.append(kwargs)
        return LLMResult(
            text='{"answers": {"1": "The SI unit is metre."}}',
            provider="gemini",
            model="gemini-3.6-flash",
            tokens_in=12,
            tokens_out=18,
            latency_ms=90,
        )

    monkeypatch.setattr(vision, "generate_llm", fake_generate_llm)

    answers, result = await vision.extract_answers_from_image(
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
        question_schema=[{"no": 1, "max_marks": 2}],
        rubrics={"1": {"question_text": "Name the SI unit of length."}},
    )

    assert answers == {"1": "The SI unit is metre."}
    assert result is not None
    assert calls[0]["provider_name"] == "gemini"
    assert calls[0]["model"] == "gemini-3.6-flash"
    assert calls[0]["feature"] == "answer_sheet_vision"
    assert calls[0]["caller"] == "extract_answers_from_image"


@pytest.mark.asyncio
async def test_unsupported_mime_does_not_invoke_gateway(monkeypatch):
    monkeypatch.setattr(vision.settings, "AEI_HANDWRITING_OCR_PHASE1_ENABLED", True)
    monkeypatch.setattr(vision, "_vision_primary_provider", lambda: "gemini")

    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("gateway should not be invoked for unsupported MIME")

    monkeypatch.setattr(vision, "generate_llm", fail_if_called)

    answers, result = await vision.extract_answers_from_image(
        image_bytes=b"not-image",
        mime_type="application/pdf",
        question_schema=[{"no": 1, "max_marks": 2}],
        rubrics={},
    )

    assert answers == {}
    assert result is None


@pytest.mark.asyncio
async def test_malformed_gateway_json_returns_safe_empty_extraction(monkeypatch):
    monkeypatch.setattr(vision.settings, "AEI_HANDWRITING_OCR_PHASE1_ENABLED", True)
    monkeypatch.setattr(vision, "_vision_primary_provider", lambda: "gemini")
    monkeypatch.setattr(vision, "_vision_fallback_provider", lambda: None)

    async def fake_generate_llm(*_args, **_kwargs):
        return LLMResult(text="not-json", provider="gemini", model="gemini-3.6-flash")

    monkeypatch.setattr(vision, "generate_llm", fake_generate_llm)

    answers, result = await vision.extract_answers_from_image(
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
        question_schema=[{"no": 1, "max_marks": 2}],
        rubrics={},
    )

    assert answers == {}
    assert result is not None


@pytest.mark.asyncio
async def test_provider_exception_returns_safe_empty_extraction(monkeypatch):
    monkeypatch.setattr(vision.settings, "AEI_HANDWRITING_OCR_PHASE1_ENABLED", True)
    monkeypatch.setattr(vision, "_vision_primary_provider", lambda: "gemini")
    monkeypatch.setattr(vision, "_vision_fallback_provider", lambda: None)

    async def fake_generate_llm(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(vision, "generate_llm", fake_generate_llm)

    answers, result = await vision.extract_answers_from_image(
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
        question_schema=[{"no": 1, "max_marks": 2}],
        rubrics={},
    )

    assert answers == {}
    assert result is None


def test_sanitizer_failure_returns_safe_empty_extraction():
    too_long = "x" * 2001

    assert vision._parse_answers_json(f'{{"answers": {{"1": "{too_long}"}}}}') == {}


def test_answer_sheet_vision_does_not_bypass_gateway_with_provider_sdk():
    source = Path(vision.__file__).read_text(encoding="utf-8")

    assert "google.genai" not in source
    assert "genai.Client" not in source


def test_handwriting_ocr_phase1_golden_harness_cases_are_stable():
    path = (
        Path(__file__).resolve().parent
        / "golden"
        / "aei_v1"
        / "handwriting_ocr_phase1_cases.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]

    assert payload["version"] == "aei-handwriting-ocr-phase1.v1"
    assert len(case_ids) == len(set(case_ids))
    assert {
        "ocr_phase1_flag_off_001",
        "ocr_phase1_gemini_gateway_001",
        "ocr_phase1_malformed_json_001",
        "ocr_phase1_unsupported_mime_001",
    }.issubset(case_ids)
    assert all(case["expected_behavior"] for case in cases)
