"""Tests for AI credit metering."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.ai.services.ai_credits import (
    CREDIT_RULES,
    assert_credits_for_charge,
    check_ai_credits,
    credits_for_purpose,
    get_school_ai_budget,
    month_start_for_school,
)


def test_credit_rules_qp_full_is_five():
    assert credits_for_purpose("qp_full") == 5
    assert credits_for_purpose("qp_from_bank") == 2
    assert credits_for_purpose("qp_clone") == 0
    assert CREDIT_RULES["qp_regen_section"] == 2
    assert CREDIT_RULES["quality_check"] == 1


def test_billing_policy_documents_charge_at_generation():
    from app.modules.ai.services.ai_credits import BILLING_POLICY

    assert "generated" in BILLING_POLICY.lower()
    assert "reject" in BILLING_POLICY.lower()


def test_default_pilot_budget():
    school = MagicMock()
    school.settings = {}
    budget = get_school_ai_budget(school)
    assert budget["monthly_credits"] == 100
    assert budget["limits"]["qp_full_per_month"] == 5


@pytest.mark.asyncio
async def test_teacher_blocked_at_pilot_qp_cap():
    school = MagicMock()
    school.id = uuid.uuid4()
    school.settings = {
        "ai_budget": {
            "monthly_credits": 100,
            "limits": {"qp_full_per_month": 5},
        }
    }
    user_id = uuid.uuid4()
    db = AsyncMock()

    from app.modules.ai.services import ai_credits as mod
    from app.modules.ai.services.ai_credits import UsageSnapshot

    async def fake_lock(_db, _sid):
        return school

    snap = UsageSnapshot(
        budget=get_school_ai_budget(school),
        since=month_start_for_school(school),
        monthly_limit=100,
        school_used=10,
        user_limit=25,
        user_used=5,
        usage_counts={
            "qp_full": 5,
            "qp_regen_full": 0,
            "qp_regen_section": 0,
            "qp_regen_question": 0,
        },
    )

    mod._lock_school_row = fake_lock
    mod._build_usage_snapshot = AsyncMock(return_value=snap)
    with pytest.raises(HTTPException) as exc:
        await check_ai_credits(
            db, school, user_id=user_id, role="teacher", purpose_tag="qp_full"
        )
    assert exc.value.status_code == 429
    assert "pilot limit" in exc.value.detail.lower()


def test_month_start_uses_school_timezone():
    from unittest.mock import MagicMock
    from datetime import datetime
    from zoneinfo import ZoneInfo

    school = MagicMock()
    school.settings = {"timezone": "Asia/Kolkata"}
    start = month_start_for_school(school)
    ist = ZoneInfo("Asia/Kolkata")
    # Billing month start in IST, stored as UTC — should be 1st 00:00 IST converted.
    expected = datetime(2026, 6, 1, 0, 0, 0, tzinfo=ist).astimezone(start.tzinfo)
    assert start.year == expected.year and start.month == expected.month
    assert start.hour == expected.hour


@pytest.mark.asyncio
async def test_charge_blocked_when_school_cap_exceeded(db_session, test_school, teacher_user):
    from app.db.models.ai_usage import AIUsage

    test_school.settings = {
        "ai_budget": {"monthly_credits": 10, "teacher_monthly_credits": 25},
        "timezone": "Asia/Kolkata",
    }
    db_session.add(
        AIUsage(
            school_id=test_school.id,
            created_by=teacher_user.id,
            feature="question_paper",
            provider="openai",
            model="test",
            purpose_tag="qp_full",
            credits_charged=9,
            role="teacher",
        )
    )
    await db_session.flush()

    with pytest.raises(HTTPException) as exc:
        await assert_credits_for_charge(
            db_session,
            test_school.id,
            user_id=teacher_user.id,
            role="teacher",
            purpose_tag="qp_full",
            credits=5,
        )
    assert exc.value.status_code == 429
