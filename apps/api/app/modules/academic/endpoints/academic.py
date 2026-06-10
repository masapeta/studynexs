"""Academic API endpoints — classes, subjects, enrollment, parent linking."""
from __future__ import annotations

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit

settings = get_settings()
from app.core.authorization import assert_can_access_student
from app.core.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.academic.schemas.academic import (
    ClassCreate, ClassOut, ParentLinkOut, ParentLinkRequest,
    StudentEnroll, StudentOut, SubjectCreate, SubjectOut,
    TeacherMappingCreate, TeacherMappingOut,
)
from app.modules.academic.services.academic_service import AcademicService
from app.shared.schemas.common import APIResponse, PaginatedResponse

router = APIRouter()


# ── Classes ──────────────────────────────────────────────────────────────────

@router.get("/classes", response_model=PaginatedResponse[ClassOut])
async def list_classes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    classes, total = await service.list_classes(uuid.UUID(current_user.school_id), page, page_size)
    return PaginatedResponse(
        items=[ClassOut.model_validate(c) for c in classes],
        total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/classes", response_model=APIResponse[ClassOut], status_code=201)
async def create_class(
    body: ClassCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    cls = await service.create_class(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=ClassOut.model_validate(cls), message="Class created")


@router.get("/classes/{class_id}", response_model=APIResponse[ClassOut])
async def get_class(
    class_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    cls = await service.get_class(uuid.UUID(current_user.school_id), class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return APIResponse(data=ClassOut.model_validate(cls))


# ── Subjects ─────────────────────────────────────────────────────────────────

@router.get("/subjects", response_model=APIResponse[list[SubjectOut]])
async def list_subjects(
    class_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    subjects = await service.list_subjects(uuid.UUID(current_user.school_id), class_id)
    return APIResponse(data=[SubjectOut.model_validate(s) for s in subjects])


@router.post("/subjects", response_model=APIResponse[SubjectOut], status_code=201)
async def create_subject(
    body: SubjectCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    subject = await service.create_subject(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=SubjectOut.model_validate(subject), message="Subject created")


# ── Students ─────────────────────────────────────────────────────────────────

@router.get(
    "/students",
    response_model=PaginatedResponse[StudentOut],
    dependencies=[rate_limit("academic:students")],
)
async def list_students(
    class_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = None,
    current_user: CurrentUser = Depends(
        require_roles("teacher", "class_incharge", "admin", "super_admin", "operations")
    ),
    db: AsyncSession = Depends(get_db),
):
    # Roster listing is staff-only — parents/students must not enumerate the school.
    service = AcademicService(db)
    students, total = await service.list_students(
        uuid.UUID(current_user.school_id),
        class_id,
        page,
        page_size,
        search=search,
    )
    return PaginatedResponse(
        items=students,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/students/enroll", response_model=APIResponse[StudentOut], status_code=201)
async def enroll_student(
    body: StudentEnroll,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    student = await service.enroll_student(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=StudentOut.model_validate(student), message="Student enrolled")


# ── Parent Linking ───────────────────────────────────────────────────────────

@router.post("/students/{student_id}/parents", response_model=APIResponse, status_code=201)
async def link_parent(
    student_id: uuid.UUID,
    body: ParentLinkRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    try:
        await service.link_parent(uuid.UUID(current_user.school_id), student_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return APIResponse(message="Parent linked to student")


@router.get("/students/{student_id}/parents", response_model=APIResponse[list[ParentLinkOut]])
async def get_student_parents(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_can_access_student(current_user, db, student_id)
    service = AcademicService(db)
    links = await service.get_student_parents(
        uuid.UUID(current_user.school_id), student_id
    )
    return APIResponse(data=[ParentLinkOut.model_validate(l) for l in links])


@router.get("/students/{student_id}/profile", response_model=APIResponse)
async def get_student_profile(
    student_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Consolidated student profile: info, parents/guardians, attendance, fees, transport."""
    await assert_can_access_student(current_user, db, student_id)
    profile = await AcademicService(db).student_profile(
        uuid.UUID(current_user.school_id), student_id
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return APIResponse(data=profile)


# ── Teacher Mapping ──────────────────────────────────────────────────────────

@router.post("/teacher-mappings", response_model=APIResponse[TeacherMappingOut], status_code=201)
async def map_teacher(
    body: TeacherMappingCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    service = AcademicService(db)
    mapping = await service.map_teacher(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=TeacherMappingOut.model_validate(mapping), message="Teacher mapped")
