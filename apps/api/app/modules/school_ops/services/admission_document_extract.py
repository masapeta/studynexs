"""Extract identity document numbers from admission uploads."""
from __future__ import annotations

import asyncio
import re

import structlog

from app.modules.school_ops.services.admission_document_ocr import extract_text_from_upload
from app.modules.files.services.file_validation import normalize_mime

logger = structlog.get_logger()

_DOC_TYPES = frozenset({"aadhaar", "birth_certificate", "apaar"})

_AADHAAR_RE = re.compile(r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b")
_APAAR_RE = re.compile(r"\b([0-9]{12})\b")
_BIRTH_CERT_RE = re.compile(
    r"(?:reg(?:istration)?\.?\s*(?:no|number)|certificate\s*(?:no|number)|cert\.?\s*no)"
    r"\s*[:\-#]?\s*([A-Z0-9][A-Z0-9/\-]{3,29})",
    re.IGNORECASE,
)


def normalize_aadhaar(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) == 12 else None


def normalize_apaar(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) == 12 else None


def normalize_birth_certificate_number(value: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", value.strip().upper())
    return cleaned if 4 <= len(cleaned) <= 40 else None


def parse_number_from_text(text: str, doc_type: str) -> str | None:
    if doc_type == "aadhaar":
        for match in _AADHAAR_RE.finditer(text):
            number = normalize_aadhaar(match.group(1))
            if number:
                return number
        return None
    if doc_type == "apaar":
        for match in _APAAR_RE.finditer(text):
            number = normalize_apaar(match.group(1))
            if number:
                return number
        return None
    if doc_type == "birth_certificate":
        match = _BIRTH_CERT_RE.search(text)
        if match:
            return normalize_birth_certificate_number(match.group(1))
        for token in re.findall(r"\b[A-Z0-9][A-Z0-9/\-]{5,29}\b", text.upper()):
            if any(ch.isdigit() for ch in token):
                return normalize_birth_certificate_number(token)
    return None


def _extract_document_number_sync(
    *,
    file_data: bytes,
    content_type: str,
    doc_type: str,
) -> str | None:
    if doc_type not in _DOC_TYPES:
        raise ValueError(f"Unsupported document type: {doc_type}")

    mime = normalize_mime(content_type)
    text = extract_text_from_upload(file_data=file_data, content_type=mime)
    if not text.strip():
        return None
    return parse_number_from_text(text, doc_type)


async def extract_document_number(
    *,
    file_data: bytes,
    content_type: str,
    doc_type: str,
) -> str | None:
    """Best-effort extraction via PDF text + Tesseract OCR (no LLM)."""
    return await asyncio.to_thread(
        _extract_document_number_sync,
        file_data=file_data,
        content_type=content_type,
        doc_type=doc_type,
    )
