"""Endpoint-level PDF fallback contract for critical teacher workflows."""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from pypdf import PdfReader
from sqlalchemy import select

from app.db.models.academic import Subject
from app.db.models.lesson_plan import LessonPlan
from app.db.models.report_card import ReportCard, ReportStatus
from app.db.models.student import Student
from app.db.models.user import User
from tests.conftest import access_token_for, auth_headers


class _BrokenHTML:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        raise OSError("cannot load library 'libgobject-2.0-0.dll'")


def _assert_pdf_bytes(payload: bytes, expected_text: str) -> None:
    assert payload.startswith(b"%PDF-")
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(payload)).pages)
    assert expected_text in text


@pytest.mark.asyncio
async def test_report_card_pdf_endpoint_uses_fallback_when_native_runtime_is_missing(
    client: AsyncClient,
    db_session,
    admin_user: User,
    student_user: User,
    test_school,
    test_class,
    monkeypatch,
):
    monkeypatch.setitem(sys.modules, "weasyprint", SimpleNamespace(HTML=_BrokenHTML))

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()

    report = ReportCard(
        school_id=test_school.id,
        student_id=student.id,
        class_id=test_class.id,
        created_by=admin_user.id,
        title="Term Report",
        student_name="Test Student",
        class_name="Grade 1 - A",
        subjects=[{"subject": "Maths", "marks_obtained": 80, "total_marks": 100}],
        total_obtained=Decimal("80"),
        total_max=Decimal("100"),
        percentage=Decimal("80"),
        overall_grade="A2",
        attendance_percentage=Decimal("95"),
        status=ReportStatus.DRAFT,
    )
    db_session.add(report)
    await db_session.flush()

    token = access_token_for(admin_user)
    res = await client.get(
        f"/api/v1/ai/report-cards/{report.id}/pdf",
        headers=auth_headers(token),
    )

    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith("application/pdf")
    _assert_pdf_bytes(res.content, "Test Student")


@pytest.mark.asyncio
async def test_lesson_plan_pdf_endpoint_uses_fallback_when_native_runtime_is_missing(
    client: AsyncClient,
    db_session,
    admin_user: User,
    test_school,
    test_class,
    monkeypatch,
):
    monkeypatch.setitem(sys.modules, "weasyprint", SimpleNamespace(HTML=_BrokenHTML))

    subject = Subject(school_id=test_school.id, name="Science", class_id=test_class.id)
    db_session.add(subject)
    await db_session.flush()

    plan = LessonPlan(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        created_by=admin_user.id,
        title="Heat Transfer",
        chapter="Heat",
        topic="Conduction",
        scheduled_for=date(2026, 7, 10),
        segments=[{"duration_min": 10, "activity": "Explain", "description": "Intro"}],
        learning_objectives=["Understand conduction"],
        materials=["Textbook"],
        notes="Use real-life examples",
    )
    db_session.add(plan)
    await db_session.flush()

    token = access_token_for(admin_user)
    res = await client.get(
        f"/api/v1/lesson-plans/{plan.id}/pdf",
        headers=auth_headers(token),
    )

    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith("application/pdf")
    _assert_pdf_bytes(res.content, "SCHOOL LESSON PLAN")
