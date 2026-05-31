"""Tests — object-level authorization and tenant-scoped resources."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.fee import FeeStructure, StudentFeeRecord
from app.db.models.file import FileCategory, UploadedFile
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_file_download_wrong_school_returns_404(
    client: AsyncClient,
    admin_user: User,
    db_session: AsyncSession,
):
    other_school = School(
        name="Other School",
        code="OTH",
        tenant_slug="other",
        board="CBSE",
        contact_email="o@test.com",
        contact_phone="+911111111111",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    foreign_file = UploadedFile(
        school_id=other_school.id,
        filename="secret.pdf",
        original_name="secret.pdf",
        content_type="application/pdf",
        size_bytes=10,
        category=FileCategory.DOCUMENT,
        storage_path="/tmp/unused",
        url="/api/v1/files/00000000-0000-0000-0000-000000000001",
        uploaded_by=admin_user.id,
    )
    db_session.add(foreign_file)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/files/{foreign_file.id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_cannot_pay_fees(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    fee_setup: FeeStructure,
    db_session: AsyncSession,
):
    res = await db_session.execute(
        select(Student).where(Student.user_id == student_user.id)
    )
    student = res.scalar_one()

    fee_record = StudentFeeRecord(
        school_id=admin_user.school_id,
        student_id=student.id,
        fee_structure_id=fee_setup.id,
        amount=fee_setup.amount,
        due_date=date(2026, 7, 5),
    )
    db_session.add(fee_record)
    await db_session.flush()

    token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.post(
        "/api/v1/fees/pay",
        headers=auth_headers(token),
        json={
            "fee_record_id": str(fee_record.id),
            "amount": 1000.0,
            "payment_mode": "cash",
        },
    )
    assert resp.status_code == 403
