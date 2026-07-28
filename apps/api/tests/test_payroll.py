"""Payroll — the list endpoint must be read-only; entry creation is explicit and idempotent.

Regression for a GET that silently created and persisted StaffPayrollEntry rows (fabricated
salary liabilities) with float amounts.
"""

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.db.models.school_ops import StaffPayrollEntry
from app.db.models.user import User
from app.modules.school_ops.services.ops_service import SchoolOpsService
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_payroll_list_creates_nothing(
    client, admin_user: User, teacher_user: User, db_session
):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/ops/payroll", headers=auth_headers(token))
    assert resp.status_code == 200

    data = resp.json()["data"]
    entries = data["entries"]
    teacher_row = next(e for e in entries if e["role"] == "teacher")
    assert teacher_row["status"] == "not_generated"
    assert teacher_row["entry_id"] is None
    assert teacher_row["user_id"]  # UI keys rows on user_id (entry_id may be null)
    # Money is a JSON number, not a string — Decimal must be cast at the boundary.
    assert isinstance(teacher_row["gross_amount"], (int, float))
    assert isinstance(data["total_gross"], (int, float))

    # The GET must not have persisted anything.
    count = await db_session.scalar(select(func.count()).select_from(StaffPayrollEntry))
    assert count == 0


@pytest.mark.asyncio
async def test_payroll_generate_is_explicit_and_idempotent(
    client, admin_user: User, teacher_user: User, db_session
):
    token = await get_auth_token(client, "test_admin", "Admin@123")

    r1 = await client.post("/api/v1/ops/payroll/generate", headers=auth_headers(token))
    assert r1.status_code == 200
    assert r1.json()["data"]["created"] >= 1

    service_rows = await SchoolOpsService(db_session).list_payroll(admin_user.school_id)
    teacher_service_row = next(e for e in service_rows if e["role"] == "teacher")
    assert isinstance(teacher_service_row["gross_amount"], Decimal)

    # Now the list shows a real, markable entry.
    resp = await client.get("/api/v1/ops/payroll", headers=auth_headers(token))
    teacher_row = next(e for e in resp.json()["data"]["entries"] if e["role"] == "teacher")
    assert teacher_row["entry_id"] is not None
    assert teacher_row["status"] == "pending"

    # Re-running creates nothing (idempotent — no double-mint, no unique-constraint 500).
    r2 = await client.post("/api/v1/ops/payroll/generate", headers=auth_headers(token))
    assert r2.status_code == 200
    assert r2.json()["data"]["created"] == 0
