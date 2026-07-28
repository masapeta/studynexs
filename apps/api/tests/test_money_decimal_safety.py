"""Financial correctness guards for internal Decimal arithmetic and stable API boundaries."""

from decimal import Decimal
from typing import get_args, get_type_hints

import pytest
from pydantic import ValidationError

from app.db.models.ai_usage import AIUsage
from app.db.models.fee import FeeReceipt, FeeStructure, StudentFeeRecord
from app.db.models.school_ops import LibraryIssue, SchoolExpense, StaffPayrollEntry
from app.modules.ai.gateway.pricing import estimate_cost_usd
from app.modules.fees.services.fee_service import _money_decimal, _money_json_number
from app.modules.portal.services.portal_service import _pending_balance
from app.modules.school_ops.schemas.ops import SchoolExpenseCreate


def _mapped_value_type(model: type, field_name: str) -> type:
    mapped_type = get_type_hints(model)[field_name]
    return get_args(mapped_type)[0]


def test_monetary_numeric_columns_are_typed_as_decimal() -> None:
    columns = (
        FeeStructure.__table__.c.amount,
        StudentFeeRecord.__table__.c.amount,
        StudentFeeRecord.__table__.c.paid_amount,
        FeeReceipt.__table__.c.amount_paid,
        LibraryIssue.__table__.c.fine_amount,
        StaffPayrollEntry.__table__.c.gross_amount,
        SchoolExpense.__table__.c.amount,
        AIUsage.__table__.c.cost_usd,
    )

    assert all(column.type.python_type is Decimal for column in columns)

    annotations = (
        (FeeStructure, "amount"),
        (StudentFeeRecord, "amount"),
        (StudentFeeRecord, "paid_amount"),
        (FeeReceipt, "amount_paid"),
        (LibraryIssue, "fine_amount"),
        (StaffPayrollEntry, "gross_amount"),
        (SchoolExpense, "amount"),
        (AIUsage, "cost_usd"),
    )
    assert all(_mapped_value_type(model, field) is Decimal for model, field in annotations)


def test_expense_input_enters_domain_as_validated_decimal() -> None:
    first = SchoolExpenseCreate(
        vendor="Stationery Shop",
        category="supplies",
        amount=0.10,
        expense_date="2026-07-28",
    )
    second = SchoolExpenseCreate(
        vendor="Stationery Shop",
        category="supplies",
        amount=0.20,
        expense_date="2026-07-28",
    )

    assert first.amount == Decimal("0.10")
    assert second.amount == Decimal("0.20")
    assert first.amount + second.amount == Decimal("0.30")

    with pytest.raises(ValidationError, match="decimal places"):
        SchoolExpenseCreate(
            vendor="Stationery Shop",
            category="supplies",
            amount="0.001",
            expense_date="2026-07-28",
        )


def test_fee_balance_arithmetic_is_decimal_exact() -> None:
    assert _pending_balance(Decimal("0.30"), Decimal("0.10")) == Decimal("0.20")
    assert _pending_balance(Decimal("10.00"), Decimal("12.00")) == Decimal("0.00")


def test_fee_wire_conversion_happens_only_after_decimal_computation() -> None:
    exact = _money_decimal(Decimal("1000.10")) + _money_decimal(Decimal("0.20"))

    assert exact == Decimal("1000.30")
    assert _money_json_number(exact) == 1000.3
    assert isinstance(_money_json_number(exact), float)


def test_ai_usage_cost_estimation_is_decimal_exact() -> None:
    cost = estimate_cost_usd("gpt-4o-mini", tokens_in=1000, tokens_out=1000)

    assert cost == Decimal("0.000750")
    assert isinstance(cost, Decimal)
    assert estimate_cost_usd("unknown", 1000, 1000) == Decimal("0.000000")
