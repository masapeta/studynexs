"""File upload MIME allowlist and bounded reads."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.modules.files.services.file_validation import (
    read_file_bytes_bounded,
    validate_file_upload,
)
from app.db.models.file import FileCategory
from tests.conftest import access_token_for, auth_headers

# Minimal valid PDF and 1×1 PNG for sniff tests.
_MIN_PDF = (
    b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
    b"xref\n0 3\ntrailer<</Root 1 0 R>>\n%%EOF"
)
_MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001"
    "08060000001f15c4890000000a49444154789c6300010000050001"
)


def test_validate_rejects_plain_text_for_document():
    with pytest.raises(Exception, match="not allowed"):
        validate_file_upload(
            category=FileCategory.DOCUMENT,
            content_type="text/plain",
            original_name="note.txt",
            file_data=b"hello",
        )


def test_validate_rejects_html_masquerading_as_image():
    with pytest.raises(Exception, match="Unrecognized|does not match"):
        validate_file_upload(
            category=FileCategory.ANSWER_SHEET,
            content_type="image/png",
            original_name="sheet.png",
            file_data=b"<html><script>alert(1)</script></html>",
        )


def test_validate_rejects_blocked_extension():
    with pytest.raises(Exception, match="extension not allowed"):
        validate_file_upload(
            category=FileCategory.DOCUMENT,
            content_type="application/pdf",
            original_name="evil.svg",
            file_data=_MIN_PDF,
        )


def test_validate_accepts_pdf_for_document():
    mime = validate_file_upload(
        category=FileCategory.DOCUMENT,
        content_type="application/pdf",
        original_name="receipt.pdf",
        file_data=_MIN_PDF,
    )
    assert mime == "application/pdf"


def test_validate_accepts_png_for_answer_sheet():
    mime = validate_file_upload(
        category=FileCategory.ANSWER_SHEET,
        content_type="image/png",
        original_name="scan.png",
        file_data=_MIN_PNG,
    )
    assert mime == "image/png"


def test_read_file_bytes_bounded_rejects_oversized_metadata(tmp_path):
    path = tmp_path / "big.bin"
    path.write_bytes(b"x" * 100)
    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_file_bytes_bounded(str(path), size_bytes=100, max_bytes=50)


@pytest.mark.asyncio
async def test_upload_rejects_text_plain(client: AsyncClient, admin_user):
    token = access_token_for(admin_user)
    resp = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers(token),
        files={"file": ("note.txt", b"hello", "text/plain")},
        data={"category": "document"},
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_accepts_pdf_document(client: AsyncClient, admin_user):
    token = access_token_for(admin_user)
    resp = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers(token),
        files={"file": ("note.pdf", _MIN_PDF, "application/pdf")},
        data={"category": "document"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["content_type"] == "application/pdf"
