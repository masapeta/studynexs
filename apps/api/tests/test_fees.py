import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.db.models.fee import FeeStructure, StudentFeeRecord
from app.db.models.user import User
from app.db.models.student import Student
from tests.conftest import auth_headers, get_auth_token

@pytest.mark.asyncio
async def test_pay_fee_flow(client: AsyncClient, admin_user: User, student_user: User, fee_setup: FeeStructure, db_session: AsyncSession):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)
    
    # Create a fee record for the student
    res = await db_session.execute(
        select(Student).where(Student.user_id == student_user.id)
    )
    student = res.scalar_one()

    fee_record = StudentFeeRecord(
        school_id=admin_user.school_id,
        student_id=student.id,
        fee_structure_id=fee_setup.id,
        amount=fee_setup.amount,
        due_date=date(2026, 7, 5)
    )
    db_session.add(fee_record)
    await db_session.flush()

    # 1. List student fees
    resp = await client.get(f"/api/v1/fees/student/{student.id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    # 2. Pay fee
    pay_data = {
        "fee_record_id": str(fee_record.id),
        "amount": 5000.00,
        "payment_mode": "cash"
    }
    resp = await client.post("/api/v1/fees/pay", json=pay_data, headers=headers)
    assert resp.status_code == 201
    receipt = resp.json()["data"]
    assert receipt["amount_paid"] == 5000.00
    assert receipt["receipt_number"].startswith("TST-")

    # 3. Verify record status
    # Refresh to see changes from the API call
    res = await db_session.execute(select(StudentFeeRecord).where(StudentFeeRecord.id == fee_record.id))
    fee_record = res.scalar_one()
    assert fee_record.status == "paid"
