"""Fail-safe server-side PDF rendering shared by all document services.

PDF endpoints must either return a real PDF or fail explicitly.  They must not
silently return HTML under a PDF-labelled user action.  Network and local-file
resource fetching is disabled to prevent document content from becoming an
SSRF or local-file-read primitive.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


class PDFRenderError(RuntimeError):
    """Raised when the server cannot safely produce a real PDF."""


def _deny_resource_fetch(url: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Reject every external resource requested by document HTML.

    StudyNexs render templates are self-contained.  A fetch attempt therefore
    indicates an unsafe or unsupported template resource.
    """

    del url, args, kwargs
    raise PDFRenderError("External PDF resource fetching is disabled")


def render_pdf(html_document: str, *, document_type: str) -> bytes:
    """Render self-contained HTML to PDF, or raise a generic render failure."""

    try:
        from weasyprint import HTML

        content = HTML(string=html_document, url_fetcher=_deny_resource_fetch).write_pdf()
    except PDFRenderError:
        logger.warning("pdf_resource_fetch_blocked", document_type=document_type)
        raise
    except Exception as exc:
        logger.exception(
            "pdf_render_failed",
            document_type=document_type,
            error_type=type(exc).__name__,
        )
        raise PDFRenderError("PDF rendering is temporarily unavailable") from exc

    if not content.startswith(b"%PDF-"):
        logger.error("pdf_render_invalid_output", document_type=document_type)
        raise PDFRenderError("PDF renderer returned invalid output")
    return content
