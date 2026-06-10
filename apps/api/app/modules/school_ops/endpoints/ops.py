"""School operations endpoints — library, events."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.school_ops.schemas.ops import (
    EventCreate,
    EventOut,
    LibraryBookCreate,
    LibraryBookOut,
    ResidentialAllocateRequest,
    ResidentialBlockCreate,
    TransportAssignRequest,
    TransportRouteCreate,
)
from app.modules.school_ops.services.ops_service import SchoolOpsService
from app.shared.schemas.common import APIResponse

router = APIRouter()


# ── Library ──────────────────────────────────────────────────────────────────

@router.get("/library/books", response_model=APIResponse[list[LibraryBookOut]])
async def list_books(
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchoolOpsService(db)
    books = await service.list_books(uuid.UUID(current_user.school_id), search)
    return APIResponse(data=[LibraryBookOut.model_validate(b) for b in books])


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
