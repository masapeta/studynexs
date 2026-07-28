"""Tests — receipt HTML renderer escapes school/student-controlled fields (N5)."""

from datetime import datetime, timezone

import pytest

from app.db.models.fee import FeeReceipt, PaymentMode
from app.modules.fees.services import receipt_pdf
from app.modules.fees.services.receipt_pdf import render_receipt_html


def _receipt(**overrides) -> FeeReceipt:
    """Unsaved FeeReceipt — render_receipt_html only reads attributes."""
    fields = dict(
        receipt_number="TST-2026-00001",
        student_name="Safe Student",
        class_name="Grade 1-A",
        amount_paid=1000,
        payment_mode=PaymentMode.CASH,
        fee_type="Tuition",
        paid_at=datetime.now(timezone.utc),
        school_name="Safe School",
        school_address="1 Main St",
        school_contact="+911234567890",
        school_logo_url=None,
        transaction_id=None,
        receipt_sequence=1,
    )
    fields.update(overrides)
    return FeeReceipt(**fields)


def test_receipt_html_escapes_injected_fields():
    receipt = _receipt(
        student_name="<script>alert(1)</script>",
        school_name='"><img src=x onerror=alert(1)>',
        fee_type="<b>Tuition</b>",
        transaction_id="<svg/onload=x>",
        school_logo_url='https://cdn.example/logo.png"><script>alert(1)</script>',
    )
    html_out = render_receipt_html(receipt)

    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "<svg/onload" not in html_out
    assert "onerror=alert(1)>" not in html_out
    # The logo URL cannot break out of the src attribute.
    assert 'logo.png"><script>' not in html_out


def test_receipt_logo_scheme_allowlist():
    blocked = render_receipt_html(_receipt(school_logo_url="javascript:alert(1)"))
    assert "<img" not in blocked
    assert "javascript:" not in blocked

    allowed = render_receipt_html(_receipt(school_logo_url="https://cdn.example/logo.png"))
    assert '<img class="school-logo" src="https://cdn.example/logo.png"' in allowed


def test_receipt_plain_fields_render_intact():
    html_out = render_receipt_html(_receipt())
    assert "Safe Student" in html_out
    assert "Safe School" in html_out
    assert "TST-2026-00001" in html_out


@pytest.mark.asyncio
async def test_receipt_pdf_omits_remote_logo_before_server_render(monkeypatch):
    captured: dict[str, str] = {}

    def fake_render(document: str, *, document_type: str) -> bytes:
        captured["document"] = document
        captured["type"] = document_type
        return b"%PDF-1.7\n"

    monkeypatch.setattr(receipt_pdf, "render_pdf", fake_render)
    content = await receipt_pdf.generate_receipt_pdf(
        _receipt(school_logo_url="https://tenant.example/logo.png")
    )

    assert content.startswith(b"%PDF-")
    assert captured["type"] == "fee_receipt"
    assert "tenant.example" not in captured["document"]
