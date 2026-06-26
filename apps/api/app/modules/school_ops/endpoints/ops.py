"""School operations endpoints — library, events."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.db.models.school_ops import AdmissionStage
from app.modules.school_ops.schemas.ops import (
    AdmissionCandidateCreate,
    AdmissionDocumentExtractRequest,
    AdmissionStageUpdate,
    EventCreate,
    EventOut,
    LibraryBookCreate,
    LibraryBookOut,
    ResidentialAllocateRequest,
    ResidentialBlockCreate,
    SchoolExpenseCreate,
    StaffOnboardCreate,
    TransportAssignRequest,
    TransportRouteCreate,
)
from app.modules.school_ops.services.ops_service import SchoolOpsService
from app.shared.schemas.common import APIResponse

router = APIRouter()


# ── Library ──────────────────────────────────────────────────────────────────

@router.get("/library/books", response_model=APIResponse)
async def list_books(
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    books = await service.list_books(uuid.UUID(current_user.school_id), search)
    return APIResponse(data=books)


@router.post("/library/books", response_model=APIResponse[LibraryBookOut], status_code=201)
async def add_book(
    body: LibraryBookCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    book = await service.add_book(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=LibraryBookOut.model_validate(book), message="Book added")


@router.post("/library/books/{book_id}/issue", response_model=APIResponse)
async def issue_book(
    book_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        await service.issue_book(uuid.UUID(current_user.school_id), book_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(message="Book issued")


@router.post("/library/issues/{issue_id}/return", response_model=APIResponse)
async def return_book(
    issue_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        await service.return_book(uuid.UUID(current_user.school_id), issue_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(message="Book returned")


# ── Events ───────────────────────────────────────────────────────────────────

@router.get("/events", response_model=APIResponse[list[EventOut]])
async def list_events(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    events = await service.list_events(uuid.UUID(current_user.school_id))
    return APIResponse(data=[EventOut.model_validate(e) for e in events])


@router.post("/events", response_model=APIResponse[EventOut], status_code=201)
async def create_event(
    body: EventCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    event = await service.create_event(
        uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
    )
    return APIResponse(data=EventOut.model_validate(event), message="Event created")


# ── Transport ──────────────────────────────────────────────────────────────────

@router.get("/transport/routes", response_model=APIResponse)
async def list_transport_routes(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    routes = await service.list_transport_routes(uuid.UUID(current_user.school_id))
    return APIResponse(data=routes)


@router.post("/transport/routes", response_model=APIResponse, status_code=201)
async def create_transport_route(
    body: TransportRouteCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    route = await service.create_route(uuid.UUID(current_user.school_id), body)
    return APIResponse(
        data={"id": str(route.id), "route_name": route.route_name}, message="Route created"
    )


@router.get("/transport/routes/{route_id}/students", response_model=APIResponse)
async def list_route_students(
    route_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        students = await service.list_route_students(uuid.UUID(current_user.school_id), route_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(data=students)


@router.post("/transport/assign", response_model=APIResponse)
async def assign_transport(
    body: TransportAssignRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        await service.assign_student_transport(uuid.UUID(current_user.school_id), body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(message="Student assigned to route")


# ── Residential ────────────────────────────────────────────────────────────────

@router.get("/residential/blocks", response_model=APIResponse)
async def list_residential_blocks(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    blocks = await service.list_residential_blocks(uuid.UUID(current_user.school_id))
    return APIResponse(data=blocks)


@router.post("/residential/blocks", response_model=APIResponse, status_code=201)
async def create_residential_block(
    body: ResidentialBlockCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    block = await service.create_block(uuid.UUID(current_user.school_id), body)
    return APIResponse(
        data={"id": str(block.id), "block_name": block.block_name}, message="Block created"
    )


@router.get("/residential/blocks/{block_id}/residents", response_model=APIResponse)
async def list_block_residents(
    block_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        residents = await service.list_block_residents(uuid.UUID(current_user.school_id), block_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(data=residents)


@router.post("/residential/allocate", response_model=APIResponse)
async def allocate_resident(
    body: ResidentialAllocateRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        await service.allocate_resident(uuid.UUID(current_user.school_id), body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(message="Student allocated to block")


# ── Admissions ────────────────────────────────────────────────────────────────

@router.get("/admissions", response_model=APIResponse)
async def list_admissions(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    rows = await service.list_admissions(uuid.UUID(current_user.school_id))
    return APIResponse(
        data={
            "candidates": rows,
            "pipeline": service.admission_pipeline_counts(rows),
        }
    )


@router.post("/admissions", response_model=APIResponse, status_code=201)
async def create_admission(
    body: AdmissionCandidateCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    row = await service.create_admission(
        uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
    )
    return APIResponse(
        data={"id": str(row.id), "stage": row.stage.value},
        message="Admission enquiry recorded",
    )


@router.post("/admissions/{candidate_id}/advance", response_model=APIResponse)
async def advance_admission(
    candidate_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        row = await service.advance_admission(uuid.UUID(current_user.school_id), candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(data={"id": str(row.id), "stage": row.stage.value})


@router.post("/admissions/{candidate_id}/revert", response_model=APIResponse)
async def revert_admission(
    candidate_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        row = await service.revert_admission(uuid.UUID(current_user.school_id), candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(data={"id": str(row.id), "stage": row.stage.value})


@router.post("/admissions/extract-document-number", response_model=APIResponse)
async def extract_admission_document_number(
    body: AdmissionDocumentExtractRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        number = await service.extract_admission_document_number(
            uuid.UUID(current_user.school_id),
            body.file_id,
            body.document_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return APIResponse(data={"number": number})


@router.patch("/admissions/{candidate_id}/stage", response_model=APIResponse)
async def update_admission_stage(
    candidate_id: uuid.UUID,
    body: AdmissionStageUpdate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        row = await service.update_admission_stage(
            uuid.UUID(current_user.school_id),
            candidate_id,
            AdmissionStage(body.stage),
            body.details,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return APIResponse(data=service.admission_to_dict(row, mask_stage_pii=False))


# ── Payroll ───────────────────────────────────────────────────────────────────

@router.get("/payroll", response_model=APIResponse)
async def list_payroll(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    rows = await service.list_payroll(uuid.UUID(current_user.school_id))
    total = sum(r["gross_amount"] for r in rows)
    paid = sum(r["gross_amount"] for r in rows if r["status"] == "paid")
    return APIResponse(data={"entries": rows, "total_gross": total, "paid_gross": paid})


@router.post("/payroll/{entry_id}/mark-paid", response_model=APIResponse)
async def mark_payroll_paid(
    entry_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    try:
        await service.mark_payroll_paid(uuid.UUID(current_user.school_id), entry_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(message="Marked paid")


# ── Expenses ──────────────────────────────────────────────────────────────────

@router.get("/expenses", response_model=APIResponse)
async def list_expenses(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    rows = await service.list_expenses(uuid.UUID(current_user.school_id))
    month_total = await service.expenses_month_total(uuid.UUID(current_user.school_id))
    return APIResponse(data={"expenses": rows, "month_total": month_total})


@router.post("/expenses", response_model=APIResponse, status_code=201)
async def create_expense(
    body: SchoolExpenseCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "operations")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    row = await service.add_expense(
        uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
    )
    return APIResponse(data={"id": str(row.id)}, message="Expense recorded")


# ── Staff directory ───────────────────────────────────────────────────────────

@router.post("/staff/onboard", response_model=APIResponse, status_code=201)
async def onboard_staff(
    body: StaffOnboardCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.users.services.user_service import can_assign_role

    if not can_assign_role(current_user.role, body.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign this role.",
        )
    service = SchoolOpsService(db)
    try:
        row = await service.onboard_staff(
            uuid.UUID(current_user.school_id), body, uuid.UUID(current_user.id)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return APIResponse(data=row, message="Staff member onboarded")


@router.get("/staff-directory", response_model=APIResponse)
async def staff_directory(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "class_incharge")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    rows = await service.list_staff_directory(uuid.UUID(current_user.school_id))
    return APIResponse(data={"staff": rows, "count": len(rows)})


@router.get("/parents-directory", response_model=APIResponse)
async def parents_directory(
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "class_incharge")),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    rows = await service.list_parents_directory(uuid.UUID(current_user.school_id))
    return APIResponse(data={"parents": rows, "count": len(rows)})
