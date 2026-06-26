"""Admission document number extraction."""
from __future__ import annotations

import pytest

from app.modules.school_ops.services.admission_document_extract import (
    extract_document_number,
    normalize_aadhaar,
    normalize_apaar,
    normalize_birth_certificate_number,
    parse_number_from_text,
)


def test_parse_aadhaar_from_text():
    assert parse_number_from_text("Aadhaar No: 1234 5678 9012", "aadhaar") == "123456789012"


def test_parse_apaar_from_text():
    assert parse_number_from_text("APAAR ID 987654321098", "apaar") == "987654321098"


def test_parse_birth_certificate_from_text():
    assert (
        parse_number_from_text("Registration No: MH/2024/001234", "birth_certificate")
        == "MH/2024/001234"
    )


def test_normalize_aadhaar_rejects_short_values():
    assert normalize_aadhaar("1234") is None


def test_normalize_birth_certificate_number():
    assert normalize_birth_certificate_number("  ab/12  ") == "AB/12"


@pytest.mark.asyncio
async def test_extract_document_number_uses_ocr_text(monkeypatch):
    from app.modules.school_ops.services import admission_document_extract as mod

    monkeypatch.setattr(
        mod,
        "extract_text_from_upload",
        lambda **_: "Aadhaar No: 4321 0987 6543",
    )
    number = await extract_document_number(
        file_data=b"fake",
        content_type="image/jpeg",
        doc_type="aadhaar",
    )
    assert number == "432109876543"

