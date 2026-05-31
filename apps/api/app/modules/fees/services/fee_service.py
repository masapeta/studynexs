"""Fee service — payment processing with atomic receipt generation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.fee import (
    FeeReceipt, FeeStatus, FeeStructure, PaymentMode,
    ReceiptCounter, StudentFeeRecord,
)
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User


class FeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_student_fees(
        self, school_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[StudentFeeRecord]:
        result = await self.db.execute(
            select(StudentFeeRecord).where(
                StudentFeeRecord.school_id == school_id,
                StudentFeeRecord.student_id == student_id,
            ).order_by(StudentFeeRecord.due_date.desc())
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
    ) -> FeeReceipt:
        """
        Process payment and generate receipt atomically.
        Locks fee record + receipt counter. Idempotent on transaction_id.
        """
        if transaction_id:
            dup = await self.db.execute(
                select(FeeReceipt).where(
                    FeeReceipt.school_id == school_id,
                    FeeReceipt.transaction_id == transaction_id,
                )
            )
            existing_receipt = dup.scalar_one_or_none()
            if existing_receipt:
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

        pay_amount = Decimal(str(amount))
        total_due = Decimal(str(fee_record.amount))
        already_paid = Decimal(str(fee_record.paid_amount or 0))
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

        # 3. Atomic receipt number generation (SELECT FOR UPDATE)
        counter_result = await self.db.execute(
            select(ReceiptCounter)
            .where(ReceiptCounter.school_id == school_id)
            .with_for_update()  # ← ROW LOCK — prevents race conditions
        )
        counter = counter_result.scalar_one()
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
            amount_paid=float(pay_amount),
            payment_mode=payment_mode,
            fee_type=fee_struct.fee_type.value.title(),
            paid_at=now,
            razorpay_payment_id=razorpay_payment_id,
            transaction_id=transaction_id,
            school_name=school.name,
            school_logo_url=school.logo_url,
            school_address=school.address.get("city", "") if school.address else None,
            school_contact=school.contact_phone,
            receipt_sequence=next_seq,
        )
        self.db.add(receipt)
        await self.db.flush()

        new_paid = already_paid + pay_amount
        fee_record.paid_amount = float(new_paid)
        fee_record.paid_at = now
        fee_record.payment_mode = payment_mode
        fee_record.razorpay_payment_id = razorpay_payment_id
        fee_record.receipt_id = receipt.id
        fee_record.status = (
            FeeStatus.PAID if new_paid >= total_due else FeeStatus.PARTIAL
        )

        await self.db.flush()
        return receipt

    async def get_fee_stats(self, school_id: uuid.UUID) -> dict:
        """Get aggregate fee stats for the dashboard."""
        from sqlalchemy import func
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total Collected (this year - simplified)
        total_collected_query = select(func.sum(FeeReceipt.amount_paid)).where(
            FeeReceipt.school_id == school_id
        )
        total_collected = await self.db.scalar(total_collected_query) or 0.0

        # Pending Fees
        pending_fees_query = select(func.sum(StudentFeeRecord.amount - StudentFeeRecord.paid_amount)).where(
            StudentFeeRecord.school_id == school_id,
            StudentFeeRecord.status != FeeStatus.PAID
        )
        pending_amount = await self.db.scalar(pending_fees_query) or 0.0

        # This Month
        this_month_query = select(func.sum(FeeReceipt.amount_paid)).where(
            FeeReceipt.school_id == school_id,
            FeeReceipt.paid_at >= current_month_start
        )
        this_month = await self.db.scalar(this_month_query) or 0.0

        return {
            "total_collected": float(total_collected),
            "pending_amount": float(pending_amount),
            "this_month": float(this_month)
        }

    async def get_recent_payments(self, school_id: uuid.UUID, limit: int = 10) -> list[FeeReceipt]:
        """Get recent fee receipts."""
        result = await self.db.execute(
            select(FeeReceipt).where(
                FeeReceipt.school_id == school_id
            ).order_by(FeeReceipt.paid_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
