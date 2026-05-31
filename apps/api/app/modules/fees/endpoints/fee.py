"""Fee endpoints — list fees, pay, get receipt."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit

settings = get_settings()
from app.core.authorization import assert_can_access_student, assert_can_pay_fee
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.fees.schemas.fee import FeeRecordOut, PayFeeRequest, ReceiptOut
from app.modules.fees.services.fee_service import FeeService
from app.shared.schemas.common import APIResponse

router = APIRouter()


@router.get("/stats", response_model=APIResponse)
async def get_fee_stats(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    stats = await service.get_fee_stats(uuid.UUID(current_user.school_id))
    return APIResponse(data=stats)


@router.get("/recent", response_model=APIResponse[list[ReceiptOut]])
async def get_recent_payments(
    limit: int = 10,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "teacher")),
    db: AsyncSession = Depends(get_db),
):
    service = FeeService(db)
    receipts = await service.get_recent_payments(uuid.UUID(current_user.school_id), limit)
    return APIResponse(data=[ReceiptOut.model_validate(r) for r in receipts])


@router.get("/student/{student_id}", response_model=APIResponse[list[FeeRecordOut]])
async def list_student_fees(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_can_access_student(current_user, db, student_id)
    service = FeeService(db)
    records = await service.list_student_fees(uuid.UUID(current_user.school_id), student_id)
    return APIResponse(data=[FeeRecordOut.model_validate(r) for r in records])


@router.post(
    "/pay",
    response_model=APIResponse[ReceiptOut],
    status_code=201,
    dependencies=[
        rate_limit("fees:pay", max_requests=settings.API_RATE_LIMIT_WRITE_PER_MIN)
    ],
)
async def pay_fee(
    body: PayFeeRequest,
    current_user: CurrentUser = Depends(
        require_roles("admin", "super_admin", "parent", "operations")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Process fee payment and generate receipt atomically."""
    await assert_can_pay_fee(current_user, db, body.fee_record_id)
    service = FeeService(db)
    try:
        receipt = await service.process_payment(
            school_id=uuid.UUID(current_user.school_id),
            fee_record_id=body.fee_record_id,
            amount=body.amount,
            payment_mode=body.payment_mode,
            razorpay_payment_id=body.razorpay_payment_id,
            transaction_id=body.transaction_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return APIResponse(data=ReceiptOut.model_validate(receipt), message="Payment successful")


@router.get("/receipt/{receipt_number}")
async def download_receipt(
    receipt_number: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download fee receipt as PDF (or HTML fallback)."""
    from sqlalchemy import select
    from fastapi.responses import Response

    from app.db.models.fee import FeeReceipt
    from app.modules.fees.services.receipt_pdf import generate_receipt_pdf

    result = await db.execute(
        select(FeeReceipt).where(
            FeeReceipt.receipt_number == receipt_number,
            FeeReceipt.school_id == uuid.UUID(current_user.school_id),
        )
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    pdf_bytes = await generate_receipt_pdf(receipt)

    # Check if it's actual PDF or HTML fallback
    content_type = "application/pdf" if pdf_bytes[:4] == b"%PDF" else "text/html"
    filename = f"{receipt_number}.pdf" if content_type == "application/pdf" else f"{receipt_number}.html"

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
