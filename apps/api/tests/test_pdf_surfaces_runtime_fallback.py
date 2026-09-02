"""Runtime contract: all document PDF surfaces stay available via fallback rendering."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

from app.modules.ai.services.paper_pdf import generate_blueprint_pdf, generate_paper_pdf
from app.modules.ai.services.report_card_pdf import generate_report_pdf
from app.modules.curriculum.services.lesson_plan_pdf import generate_lesson_plan_pdf
from app.modules.fees.services.receipt_pdf import generate_receipt_pdf


class _BrokenHTML:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        raise OSError("cannot load library 'libgobject-2.0-0.dll'")


def _assert_real_pdf(payload: bytes) -> None:
    assert payload.startswith(b"%PDF-")
    assert len(PdfReader(BytesIO(payload)).pages) >= 1


@pytest.mark.asyncio
async def test_all_five_pdf_surfaces_render_when_native_runtime_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "weasyprint", SimpleNamespace(HTML=_BrokenHTML))

    payment_mode = SimpleNamespace(value="cash")
    receipt = SimpleNamespace(
        school_name="StudyNexs School",
        school_address="Main Road",
        school_contact="+91 9000000000",
        student_name="Ansh Patel",
        class_name="Grade 6-A",
        fee_type="Tuition",
        receipt_number="RCPT-001",
        transaction_id="TXN-001",
        school_logo_url=None,
        paid_at=datetime.now(timezone.utc),
        payment_mode=payment_mode,
        amount_paid=Decimal("1500.00"),
    )

    report = SimpleNamespace(
        title="Term Report",
        student_name="Ansh Patel",
        class_name="Grade 6-A",
        subjects=[{"subject": "Maths", "marks_obtained": 78, "total_marks": 100}],
        total_obtained=Decimal("78"),
        total_max=Decimal("100"),
        percentage=Decimal("78"),
        overall_grade="B1",
        attendance_percentage=Decimal("92"),
        not_assessed=["Science"],
        ai_remark="Steady progress with clear improvement in problem solving.",
    )

    paper = SimpleNamespace(
        board="SSC",
        title="Unit Test 1",
        grade="Grade 6",
        subject_name="Science",
        duration_minutes=45,
        total_marks=Decimal("25"),
        exam_type=SimpleNamespace(value="unit_test"),
        general_instructions="Answer all questions.",
        sections=[
            {
                "title": "Section A",
                "instructions": "Choose the right answer.",
                "questions": [
                    {
                        "number": 1,
                        "text": "Water boils at what temperature?",
                        "marks": 1,
                        "options": ["50C", "100C", "150C", "200C"],
                        "answer_key": "100C",
                        "type": "mcq",
                        "chapter": "Heat",
                        "bloom": "Remember",
                    }
                ],
            }
        ],
    )

    receipt_pdf = await generate_receipt_pdf(receipt)
    report_pdf, report_media_type = generate_report_pdf(report, school_name="StudyNexs School")
    paper_pdf, paper_media_type = generate_paper_pdf(paper, school_name="StudyNexs School")
    blueprint_pdf, blueprint_media_type = generate_blueprint_pdf(
        paper, school_name="StudyNexs School"
    )
    lesson_pdf, lesson_media_type = generate_lesson_plan_pdf(
        teacher_name="Teacher One",
        subject_name="Science",
        class_label="Grade 6-A",
        scheduled_for=datetime.now(timezone.utc).date(),
        topic="Heat",
        duration_minutes=45,
        learning_objectives=["Define heat", "Differentiate conduction and convection"],
        materials=["Textbook", "Board"],
        segments=[
            {
                "duration_min": 10,
                "activity": "Explain concept",
                "description": "Introduce heat transfer",
                "notes": "Use chapter examples",
            }
        ],
    )

    assert report_media_type == "application/pdf"
    assert paper_media_type == "application/pdf"
    assert blueprint_media_type == "application/pdf"
    assert lesson_media_type == "application/pdf"

    _assert_real_pdf(receipt_pdf)
    _assert_real_pdf(report_pdf)
    _assert_real_pdf(paper_pdf)
    _assert_real_pdf(blueprint_pdf)
    _assert_real_pdf(lesson_pdf)
