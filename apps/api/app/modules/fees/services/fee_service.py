"""Fee service — payment processing with atomic receipt generation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.fee import (
    FeeReceipt,
    FeeStatus,
    FeeStructure,
    PaymentMode,
    ReceiptCounter,
    StudentFeeRecord,
)
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User

_ZERO_MONEY = Decimal("0.00")


def _money_decimal(value: Decimal | int | float | str | None) -> Decimal:
    """Return an exact value for internal monetary arithmetic.

    Database ``Numeric`` values and validated payment inputs are already ``Decimal``.  The
    fallback conversion exists only for legacy/test callers and converts through text so a
    binary float never participates in arithmetic.
    """
    if value is None:
        return _ZERO_MONEY
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money_json_number(value: Decimal) -> float:
    """Preserve the established /api/v1 JSON-number contract at the response boundary."""
    return float(value)


def _default_receipt_prefix(school: School) -> str:
    """Receipt prefix used when a school's counter wasn't provisioned at onboarding."""
    base = "".join(ch for ch in (school.code or "") if ch.isalnum()).upper()
    return (base or "RCPT")[:10]


class FeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_student_fees(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[StudentFeeRecord]:
        result = await self.db.execute(
            select(StudentFeeRecord)
            .where(
                StudentFeeRecord.school_id == school_id,
                StudentFeeRecord.student_id == student_id,
            )
            .order_by(StudentFeeRecord.due_date.desc())
        )
        return list(result.scalars().all())

    async def process_payment(
        self,
        school_id: uuid.UUID,
        fee_record_id: uuid.UUID,
        amount: Decimal,
        payment_mode: PaymentMode,
        razorpay_payment_id: str | None = None,
        transaction_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> FeeReceipt:
        """
        Process payment and generate receipt atomically.
        Locks fee record + receipt counter. Idempotent on transaction_id / idempotency_key
        (sequential retries return the existing receipt; truly-concurrent dups hit the partial
        unique index and surface as a 409).
        """
        pay_amount = _money_decimal(amount)
        for field, value in (
            ("transaction_id", transaction_id),
            ("idempotency_key", idempotency_key),
        ):
            if value:
                existing_receipt = (
                    await self.db.execute(
                        select(FeeReceipt).where(
                            FeeReceipt.school_id == school_id,
                            getattr(FeeReceipt, field) == value,
                        )
                    )
                ).scalar_one_or_none()
                if existing_receipt:
                    # Idempotent replay only when the key is reused for the SAME amount. A key
                    # reused with a different amount is a client error — returning the earlier
                    # (unrelated) receipt would silently mis-record the new payment.
                    if _money_decimal(existing_receipt.amount_paid) != pay_amount:
                        raise ValueError(
                            f"{field} was already used for a payment of a different amount"
                        )
                    return existing_receipt

        result = await self.db.execute(
            select(StudentFeeRecord)
            .where(
                StudentFeeRecord.id == fee_record_id,
                StudentFeeRecord.school_id == school_id,
            )
            .with_for_update()
        )
        fee_record = result.scalar_one_or_none()
        if not fee_record:
            raise ValueError("Fee record not found")

        if fee_record.status == FeeStatus.PAID:
            raise ValueError("Fee already paid")

        total_due = _money_decimal(fee_record.amount)
        already_paid = _money_decimal(fee_record.paid_amount)
        remaining = total_due - already_paid

        if pay_amount > remaining:
            raise ValueError("Payment amount exceeds remaining balance")

        # 2. Get student and school info for receipt snapshot
        student_result = await self.db.execute(
            select(Student).where(Student.id == fee_record.student_id)
        )
        student = student_result.scalar_one()

        user_result = await self.db.execute(select(User).where(User.id == student.user_id))
        student_user = user_result.scalar_one()

        school_result = await self.db.execute(select(School).where(School.id == school_id))
        school = school_result.scalar_one()

        fee_struct_result = await self.db.execute(
            select(FeeStructure).where(FeeStructure.id == fee_record.fee_structure_id)
        )
        fee_struct = fee_struct_result.scalar_one()

        from app.db.models.academic import Class

        class_result = await self.db.execute(select(Class).where(Class.id == student.class_id))
        cls = class_result.scalar_one()

        # 3. Atomic receipt number generation (SELECT FOR UPDATE). Self-provision the
        # per-school counter if onboarding didn't create one — idempotent and race-safe via
        # the unique school_id constraint — so the first-ever payment can't crash.
        counter = (
            await self.db.execute(
                select(ReceiptCounter)
                .where(ReceiptCounter.school_id == school_id)
                .with_for_update()  # ← ROW LOCK — prevents race conditions
            )
        ).scalar_one_or_none()
        if counter is None:
            await self.db.execute(
                pg_insert(ReceiptCounter)
                .values(
                    school_id=school_id,
                    prefix=_default_receipt_prefix(school),
                    last_sequence=0,
                )
                .on_conflict_do_nothing(index_elements=["school_id"])
            )
            await self.db.flush()
            counter = (
                await self.db.execute(
                    select(ReceiptCounter)
                    .where(ReceiptCounter.school_id == school_id)
                    .with_for_update()
                )
            ).scalar_one()
        counter.last_sequence += 1
        next_seq = counter.last_sequence
        year = datetime.now(timezone.utc).year
        receipt_number = f"{counter.prefix}-{year}-{next_seq:05d}"

        now = datetime.now(timezone.utc)

        # 4. Create receipt (immutable snapshot)
        receipt = FeeReceipt(
            school_id=school_id,
            receipt_number=receipt_number,
            student_id=student.id,
            student_name=student_user.full_name,
            class_name=f"{cls.grade}-{cls.section}",
            amount_paid=pay_amount,
            payment_mode=payment_mode,
            fee_type=fee_struct.fee_type.value.title(),
            paid_at=now,
            razorpay_payment_id=razorpay_payment_id,
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            school_name=school.name,
            school_logo_url=school.logo_url,
            school_address=school.address.get("city", "") if school.address else None,
            school_contact=school.contact_phone,
            receipt_sequence=next_seq,
        )
        self.db.add(receipt)
        await self.db.flush()

        new_paid = already_paid + pay_amount
        fee_record.paid_amount = new_paid
        fee_record.paid_at = now
        fee_record.payment_mode = payment_mode
        fee_record.razorpay_payment_id = razorpay_payment_id
        fee_record.receipt_id = receipt.id
        fee_record.status = FeeStatus.PAID if new_paid >= total_due else FeeStatus.PARTIAL

        await self.db.flush()
        return receipt

    async def get_fee_stats(self, school_id: uuid.UUID) -> dict:
        """Get aggregate fee stats for the dashboard."""
        from datetime import datetime, timezone

        from sqlalchemy import func

        now = datetime.now(timezone.utc)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total Collected (this year - simplified)
        total_collected_query = select(func.sum(FeeReceipt.amount_paid)).where(
            FeeReceipt.school_id == school_id
        )
        total_collected = _money_decimal(await self.db.scalar(total_collected_query))

        # Pending Fees
        pending_fees_query = select(
            func.sum(StudentFeeRecord.amount - StudentFeeRecord.paid_amount)
        ).where(StudentFeeRecord.school_id == school_id, StudentFeeRecord.status != FeeStatus.PAID)
        pending_amount = _money_decimal(await self.db.scalar(pending_fees_query))

        pending_families_query = select(
            func.count(func.distinct(StudentFeeRecord.student_id))
        ).where(
            StudentFeeRecord.school_id == school_id,
            StudentFeeRecord.status != FeeStatus.PAID,
            StudentFeeRecord.amount > StudentFeeRecord.paid_amount,
        )
        pending_families = int(await self.db.scalar(pending_families_query) or 0)

        # This Month
        this_month_query = select(func.sum(FeeReceipt.amount_paid)).where(
            FeeReceipt.school_id == school_id, FeeReceipt.paid_at >= current_month_start
        )
        this_month = _money_decimal(await self.db.scalar(this_month_query))

        return {
            "total_collected": _money_json_number(total_collected),
            "pending_amount": _money_json_number(pending_amount),
            "pending_families": pending_families,
            "this_month": _money_json_number(this_month),
        }

    async def get_recent_payments(self, school_id: uuid.UUID, limit: int = 10) -> list[FeeReceipt]:
        """Get recent fee receipts."""
        result = await self.db.execute(
            select(FeeReceipt)
            .where(FeeReceipt.school_id == school_id)
            .order_by(FeeReceipt.paid_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_fee_roster(self, school_id: uuid.UUID) -> dict:
        """Per-student fee summary for the admin fees screen."""
        from app.db.models.academic import Class
        from app.db.models.student import Student
        from app.db.models.user import User

        rows = (
            await self.db.execute(
                select(
                    Student.id,
                    User.full_name,
                    Class.grade,
                    Class.section,
                    func.coalesce(func.sum(StudentFeeRecord.amount), 0).label("total_due"),
                    func.coalesce(func.sum(StudentFeeRecord.paid_amount), 0).label("total_paid"),
                )
                .join(User, User.id == Student.user_id)
                .join(Class, Class.id == Student.class_id)
                .outerjoin(
                    StudentFeeRecord,
                    (StudentFeeRecord.student_id == Student.id)
                    & (StudentFeeRecord.school_id == school_id),
                )
                .where(Student.school_id == school_id)
                .group_by(Student.id, User.full_name, Class.grade, Class.section)
                .order_by(User.full_name)
            )
        ).all()

        # Each still-owing student's earliest-due unpaid record — the target the "Record
        # payment" action pays against. One bounded query (not per student); keep the first
        # row per student (earliest due). Replaces a broken `min(id)` aggregate: Postgres has
        # no min(uuid), so the previous roster query 500'd outright.
        next_record: dict[uuid.UUID, uuid.UUID] = {}
        owing_rows = (
            await self.db.execute(
                select(StudentFeeRecord.student_id, StudentFeeRecord.id)
                .where(
                    StudentFeeRecord.school_id == school_id,
                    StudentFeeRecord.status != FeeStatus.PAID,
                )
                .order_by(
                    StudentFeeRecord.student_id,
                    StudentFeeRecord.due_date.asc(),
                    StudentFeeRecord.id,
                )
            )
        ).all()
        for stud_id, rec_id in owing_rows:
            next_record.setdefault(stud_id, rec_id)

        overdue_set = set(
            (
                await self.db.execute(
                    select(StudentFeeRecord.student_id).where(
                        StudentFeeRecord.school_id == school_id,
                        StudentFeeRecord.status == FeeStatus.OVERDUE,
                    )
                )
            )
            .scalars()
            .all()
        )

        students_out = []
        # Accumulate money in Decimal — summing per-student floats drifts (money is exact).
        total_due_all = Decimal("0")
        total_paid_all = Decimal("0")
        for sid, name, grade, section, total_due, total_paid in rows:
            due = _money_decimal(total_due)
            paid = _money_decimal(total_paid)
            total_due_all += due
            total_paid_all += paid
            # paid (nothing owed or fully covered) → overdue → partially paid → pending.
            # The previous chain made the 'pending' case unreachable and mislabeled
            # never-paid students as 'partial'.
            if due <= 0 or paid >= due:
                status = "paid"
            elif sid in overdue_set:
                status = "overdue"
            elif paid > 0:
                status = "partial"
            else:
                status = "pending"
            record_id = next_record.get(sid)
            students_out.append(
                {
                    "student_id": str(sid),
                    "name": name,
                    "class_label": f"{grade} {section}".strip(),
                    "total_due": _money_json_number(due),
                    "paid_amount": _money_json_number(paid),
                    "status": status,
                    "fee_record_id": str(record_id) if record_id else None,
                }
            )

        return {
            "students": students_out,
            "total_due": _money_json_number(total_due_all),
            "total_collected": _money_json_number(total_paid_all),
            "term_label": "Term 1",
        }
