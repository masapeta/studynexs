from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.fee import FeeStructure, StudentFeeRecord
from app.db.models.student import Student
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_pay_fee_flow(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    fee_setup: FeeStructure,
    db_session: AsyncSession,
):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)

    # Create a fee record for the student
    res = await db_session.execute(select(Student).where(Student.user_id == student_user.id))
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

    # 1. List student fees
    resp = await client.get(f"/api/v1/fees/student/{student.id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    # 2. Pay fee
    pay_data = {"fee_record_id": str(fee_record.id), "amount": 5000.00, "payment_mode": "cash"}
    resp = await client.post("/api/v1/fees/pay", json=pay_data, headers=headers)
    assert resp.status_code == 201
    receipt = resp.json()["data"]
    assert receipt["amount_paid"] == 5000.00
    assert receipt["receipt_number"].startswith("TST-")

    # 3. Verify record status
    # Refresh to see changes from the API call
    res = await db_session.execute(
        select(StudentFeeRecord).where(StudentFeeRecord.id == fee_record.id)
    )
    fee_record = res.scalar_one()
    assert fee_record.status == "paid"


async def _make_fee_record(db_session, admin_user, student_user, fee_setup) -> StudentFeeRecord:
    res = await db_session.execute(select(Student).where(Student.user_id == student_user.id))
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
    return fee_record


@pytest.mark.asyncio
async def test_parent_cannot_self_record_payment(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    parent_user: User,
    fee_setup: FeeStructure,
    db_session: AsyncSession,
):
    """Sev-1 regression: a parent must not be able to mark their child's fee PAID.

    The /pay endpoint records offline collections attested by school staff; without a
    signature-verified gateway, admitting `parent` let a parent self-clear fees and mint an
    official receipt with no money movement. Parents are no longer in the role gate.
    """
    fee_record = await _make_fee_record(db_session, admin_user, student_user, fee_setup)
    token = await get_auth_token(client, "test_parent", "Parent@123")
    resp = await client.post(
        "/api/v1/fees/pay",
        headers=auth_headers(token),
        json={"fee_record_id": str(fee_record.id), "amount": 5000.00, "payment_mode": "cash"},
    )
    assert resp.status_code == 403
    # And the fee stays unpaid.
    res = await db_session.execute(
        select(StudentFeeRecord).where(StudentFeeRecord.id == fee_record.id)
    )
    assert res.scalar_one().status != "paid"


@pytest.mark.asyncio
async def test_online_payment_rejected_without_verified_gateway(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    fee_setup: FeeStructure,
    db_session: AsyncSession,
):
    """Even staff cannot record an `online`/gateway-claimed payment here — that requires the
    signature-verified Razorpay flow (not yet built). Guards against forged gateway references."""
    fee_record = await _make_fee_record(db_session, admin_user, student_user, fee_setup)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)

    online = await client.post(
        "/api/v1/fees/pay",
        headers=headers,
        json={"fee_record_id": str(fee_record.id), "amount": 5000.00, "payment_mode": "online"},
    )
    assert online.status_code == 400

    forged = await client.post(
        "/api/v1/fees/pay",
        headers=headers,
        json={
            "fee_record_id": str(fee_record.id),
            "amount": 5000.00,
            "payment_mode": "cash",
            "razorpay_payment_id": "pay_forged123",
        },
    )
    assert forged.status_code == 400

    res = await db_session.execute(
        select(StudentFeeRecord).where(StudentFeeRecord.id == fee_record.id)
    )
    assert res.scalar_one().status != "paid"


@pytest.mark.asyncio
async def test_idempotency_key_reuse_with_different_amount_is_rejected(
    admin_user: User, student_user: User, fee_setup, db_session
):
    """Regression: a reused idempotency key must not silently return an unrelated receipt.

    Same key + same amount → idempotent replay (same receipt). Same key + different amount →
    rejected, so a second, different payment can't be mis-recorded as the first.
    """
    from decimal import Decimal

    from app.db.models.fee import PaymentMode
    from app.modules.fees.services.fee_service import FeeService

    fee_record = await _make_fee_record(db_session, admin_user, student_user, fee_setup)
    svc = FeeService(db_session)

    first = await svc.process_payment(
        school_id=fee_record.school_id,
        fee_record_id=fee_record.id,
        amount=Decimal("2000.00"),
        payment_mode=PaymentMode.CASH,
        idempotency_key="key-1",
    )
    replay = await svc.process_payment(
        school_id=fee_record.school_id,
        fee_record_id=fee_record.id,
        amount=Decimal("2000.00"),
        payment_mode=PaymentMode.CASH,
        idempotency_key="key-1",
    )
    assert replay.id == first.id  # idempotent

    with pytest.raises(ValueError):
        await svc.process_payment(
            school_id=fee_record.school_id,
            fee_record_id=fee_record.id,
            amount=Decimal("3000.00"),
            payment_mode=PaymentMode.CASH,
            idempotency_key="key-1",
        )


@pytest.mark.asyncio
async def test_roster_labels_never_paid_student_pending(
    client: AsyncClient, admin_user: User, student_user: User, fee_setup, db_session
):
    """Regression: a never-paid, non-overdue student is 'pending', not 'partial'.

    The old status chain made the 'pending' branch unreachable and mislabeled these students.
    """
    fee_record = await _make_fee_record(db_session, admin_user, student_user, fee_setup)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/fees/roster", headers=auth_headers(token))
    assert resp.status_code == 200
    students = resp.json()["data"]["students"]
    row = next(s for s in students if s["student_id"] == str(fee_record.student_id))
    assert row["status"] == "pending"
