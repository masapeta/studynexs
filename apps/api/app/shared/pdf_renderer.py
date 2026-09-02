"""Fail-safe server-side PDF rendering shared by all document services.

PDF endpoints must either return a real PDF or fail explicitly.  They must not
silently return HTML under a PDF-labelled user action.  Network and local-file
resource fetching is disabled to prevent document content from becoming an
SSRF or local-file-read primitive.
"""

from __future__ import annotations

import html
import re
import textwrap
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


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _html_to_lines(html_document: str) -> list[str]:
    scrubbed = re.sub(r"(?is)<(script|style)\\b.*?>.*?</\\1>", " ", html_document)
    scrubbed = re.sub(r"(?i)<\\s*br\\s*/?\\s*>", "\n", scrubbed)
    block_close_tags = (
        r"(?i)</(p|div|li|tr|h1|h2|h3|h4|h5|h6|section|article|header|footer)>"
    )
    scrubbed = re.sub(block_close_tags, "\n", scrubbed)
    scrubbed = re.sub(r"(?is)<[^>]+>", " ", scrubbed)
    decoded = html.unescape(scrubbed)

    lines: list[str] = []
    for raw in decoded.splitlines():
        normalized = " ".join(raw.split())
        if not normalized:
            continue
        lines.extend(textwrap.wrap(normalized, width=95) or [normalized])
    return lines


def _page_stream(lines: list[str]) -> bytes:
    chunks = ["BT", "/F1 10 Tf", "50 800 Td"]
    for index, line in enumerate(lines):
        if index > 0:
            chunks.append("0 -14 Td")
        chunks.append(f"({_escape_pdf_text(line)}) Tj")
    chunks.append("ET")
    return "\n".join(chunks).encode("latin-1", errors="replace")


def _render_fallback_pdf(html_document: str, *, document_type: str) -> bytes:
    lines = _html_to_lines(html_document)
    if not lines:
        lines = ["StudyNexs document", "No printable text content was found."]

    # A4 page with conservative line count at 10pt / 14pt leading.
    page_line_limit = 52
    pages = [
        lines[i : i + page_line_limit]
        for i in range(0, len(lines), page_line_limit)
    ]
    if not pages:
        pages = [["StudyNexs document"]]

    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }

    kids: list[str] = []
    next_obj = 4
    for page_lines in pages:
        page_obj = next_obj
        content_obj = next_obj + 1
        next_obj += 2
        stream = _page_stream(page_lines)
        objects[content_obj] = (
            f"<< /Length {len(stream)} >>\n".encode("ascii")
            + b"stream\n"
            + stream
            + b"\nendstream"
        )
        objects[page_obj] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>"
        ).encode("ascii")
        kids.append(f"{page_obj} 0 R")

    objects[2] = (
        f"<< /Type /Pages /Count {len(kids)} /Kids [{' '.join(kids)}] >>"
    ).encode("ascii")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: dict[int, int] = {}
    max_obj = max(objects)
    for obj_id in range(1, max_obj + 1):
        body = objects[obj_id]
        offsets[obj_id] = len(output)
        output.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {max_obj + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, max_obj + 1):
        output.extend(f"{offsets[obj_id]:010} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )

    logger.warning(
        "pdf_render_fallback_text_used",
        document_type=document_type,
        page_count=len(kids),
        line_count=len(lines),
    )
    return bytes(output)


def render_pdf(html_document: str, *, document_type: str) -> bytes:
    """Render self-contained HTML to PDF, or raise a generic render failure."""

    try:
        from weasyprint import HTML

        content = HTML(string=html_document, url_fetcher=_deny_resource_fetch).write_pdf()
    except PDFRenderError:
        logger.warning("pdf_resource_fetch_blocked", document_type=document_type)
        raise
    except Exception as exc:
        logger.warning(
            "pdf_render_native_failed_using_text_fallback",
            document_type=document_type,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        try:
            content = _render_fallback_pdf(html_document, document_type=document_type)
        except Exception as fallback_exc:
            logger.exception(
                "pdf_render_fallback_failed",
                document_type=document_type,
                error_type=type(fallback_exc).__name__,
            )
            raise PDFRenderError("PDF rendering is temporarily unavailable") from fallback_exc

    if not content.startswith(b"%PDF-"):
        logger.error("pdf_render_invalid_output", document_type=document_type)
        raise PDFRenderError("PDF renderer returned invalid output")
    return content
