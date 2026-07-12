"""Shared document OCR and text extraction — one path for all school documents (§38.1)."""
from __future__ import annotations

import io
import shutil

import structlog

from app.core.config import get_settings
from app.modules.files.services.file_validation import IMAGE_MIMES, normalize_mime

logger = structlog.get_logger()
settings = get_settings()


def ocr_available() -> bool:
    """True when the Tesseract binary is installed and reachable."""
    try:
        import pytesseract

        cmd = settings.TESSERACT_CMD or None
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def extract_text_from_pdf(file_data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_data))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def extract_text_from_image(file_data: bytes) -> str | None:
    if not ocr_available():
        logger.info("document_ocr_unavailable", reason="tesseract_not_installed")
        return None

    from PIL import Image
    import pytesseract

    cmd = settings.TESSERACT_CMD or None
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    image = Image.open(io.BytesIO(file_data))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    return pytesseract.image_to_string(image)


def extract_text_from_upload(*, file_data: bytes, content_type: str) -> str:
    """Return best-effort plain text from a PDF or image upload."""
    mime = normalize_mime(content_type)
    if mime == "application/pdf":
        try:
            return extract_text_from_pdf(file_data)
        except Exception:
            logger.warning("document_pdf_text_extract_failed")
            return ""
    if mime in IMAGE_MIMES:
        return extract_text_from_image(file_data) or ""
    return ""


def tesseract_search_path() -> str | None:
    """Best-effort path hint for local dev (Windows installer default)."""
    if settings.TESSERACT_CMD:
        return settings.TESSERACT_CMD
    return shutil.which("tesseract")
