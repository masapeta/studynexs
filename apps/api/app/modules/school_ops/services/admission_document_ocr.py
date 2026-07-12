"""OCR and text extraction for admission identity documents.

Delegates to the shared document OCR service (§38.1) — do not duplicate extraction logic.
"""
from __future__ import annotations

from app.modules.files.services.document_ocr import (
    extract_text_from_image,
    extract_text_from_pdf,
    extract_text_from_upload,
    ocr_available,
    tesseract_search_path,
)

__all__ = [
    "extract_text_from_image",
    "extract_text_from_pdf",
    "extract_text_from_upload",
    "ocr_available",
    "tesseract_search_path",
]
