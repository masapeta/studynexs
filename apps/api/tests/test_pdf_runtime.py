"""Production-safety contract tests for truthful PDF generation."""

from __future__ import annotations

import sys
from io import BytesIO
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app.main import app
from app.shared.pdf_renderer import PDFRenderError, _deny_resource_fetch, render_pdf


def test_pdf_renderer_blocks_external_resource_fetching():
    with pytest.raises(PDFRenderError, match="resource fetching is disabled"):
        _deny_resource_fetch("https://169.254.169.254/latest/meta-data/")

    with pytest.raises(PDFRenderError, match="resource fetching is disabled"):
        _deny_resource_fetch("file:///etc/passwd")


def test_pdf_renderer_rejects_non_pdf_output(monkeypatch):
    class FakeHTML:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def write_pdf(self) -> bytes:
            return b"<html>not a pdf</html>"

    monkeypatch.setitem(sys.modules, "weasyprint", SimpleNamespace(HTML=FakeHTML))

    with pytest.raises(PDFRenderError, match="invalid output"):
        render_pdf("<p>hello</p>", document_type="test")


@pytest.mark.asyncio
async def test_pdf_render_failure_has_explicit_retryable_http_contract():
    handler = app.exception_handlers[PDFRenderError]
    request = Request(
        {"type": "http", "method": "GET", "path": "/document.pdf", "headers": []}
    )

    response = await handler(request, PDFRenderError("internal renderer detail"))

    assert response.status_code == 503
    assert response.headers["retry-after"] == "30"
    assert b"internal renderer detail" not in response.body
    assert b"temporarily unavailable" in response.body


def test_real_pdf_render_and_parse_when_native_runtime_is_available():
    try:
        import weasyprint  # noqa: F401
        from pypdf import PdfReader
    except (ImportError, OSError) as exc:
        pytest.skip(f"native PDF runtime unavailable in this environment: {exc}")

    content = render_pdf(
        "<html><meta charset='utf-8'><body>StudyNexs हिन्दी తెలుగు</body></html>",
        document_type="runtime_smoke",
    )

    assert content.startswith(b"%PDF-")
    assert len(PdfReader(BytesIO(content)).pages) == 1
