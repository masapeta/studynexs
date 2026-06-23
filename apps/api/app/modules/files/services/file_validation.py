"""Upload MIME allowlist and bounded file reads — untrusted file surface."""
from __future__ import annotations

from pathlib import Path

from app.db.models.file import FileCategory

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

IMAGE_MIMES = frozenset({"image/jpeg", "image/png", "image/webp"})

ALLOWED_MIMES_BY_CATEGORY: dict[FileCategory, frozenset[str]] = {
    FileCategory.PROFILE_PHOTO: IMAGE_MIMES,
    FileCategory.RECEIPT_PDF: frozenset({"application/pdf"}),
    FileCategory.DOCUMENT: IMAGE_MIMES | frozenset({"application/pdf"}),
    FileCategory.REPORT_CARD: frozenset({"application/pdf"}),
    FileCategory.ANSWER_SHEET: IMAGE_MIMES,
}

_BLOCKED_EXTENSIONS = frozenset({".html", ".htm", ".svg", ".js", ".mjs", ".xhtml"})


class FileUploadRejected(ValueError):
    """Client upload failed validation."""


def normalize_mime(content_type: str | None) -> str:
    return (content_type or "application/octet-stream").split(";")[0].strip().lower()


def sniff_mime(file_data: bytes) -> str | None:
    if len(file_data) >= 5 and file_data[:5] == b"%PDF-":
        return "application/pdf"
    if len(file_data) >= 3 and file_data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(file_data) >= 8 and file_data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if (
        len(file_data) >= 12
        and file_data[:4] == b"RIFF"
        and file_data[8:12] == b"WEBP"
    ):
        return "image/webp"
    return None


def validate_file_upload(
    *,
    category: FileCategory,
    content_type: str | None,
    original_name: str,
    file_data: bytes,
) -> str:
    """Return normalized allowed MIME or raise FileUploadRejected."""
    if len(file_data) > MAX_UPLOAD_BYTES:
        raise FileUploadRejected("File too large (max 10MB)")

    ext = Path(original_name).suffix.lower()
    if ext in _BLOCKED_EXTENSIONS:
        raise FileUploadRejected(f"File extension not allowed: {ext}")

    declared = normalize_mime(content_type)
    allowed = ALLOWED_MIMES_BY_CATEGORY[category]
    if declared not in allowed:
        raise FileUploadRejected(
            f"File type '{declared}' is not allowed for category '{category.value}'"
        )

    sniffed = sniff_mime(file_data)
    if sniffed is None:
        raise FileUploadRejected("Unrecognized or disallowed file content")

    if sniffed not in allowed:
        raise FileUploadRejected("File content does not match declared type")

    return sniffed


def read_file_bytes_bounded(
    storage_path: str,
    *,
    size_bytes: int,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> bytes:
    """Read an on-disk upload with a hard byte cap (defense against huge reads)."""
    if size_bytes > max_bytes:
        raise ValueError(f"File exceeds maximum size ({max_bytes} bytes)")

    path = Path(storage_path)
    if not path.is_file():
        raise ValueError("File not found on disk")

    with path.open("rb") as handle:
        data = handle.read(max_bytes + 1)

    if len(data) > max_bytes:
        raise ValueError(f"File exceeds maximum size ({max_bytes} bytes)")

    return data
