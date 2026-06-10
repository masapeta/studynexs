"""File endpoints — upload/download."""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit

settings = get_settings()
from app.core.authorization import assert_can_access_file
from app.core.dependencies import CurrentUser, get_current_user
from app.db.models.file import FileCategory
from app.modules.files.schemas.file import FileOut
from app.modules.files.services.file_service import FileService
from app.shared.schemas.common import APIResponse

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/upload",
    response_model=APIResponse[FileOut],
    status_code=201,
    dependencies=[
        rate_limit("files:upload", max_requests=settings.API_RATE_LIMIT_UPLOAD_PER_MIN)
    ],
)
async def upload_file(
    file: UploadFile = File(...),
    category: str = "document",
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file (max 10MB)."""
    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        cat = FileCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    service = FileService(db)
    record = await service.upload(
        school_id=uuid.UUID(current_user.school_id),
        file_data=file_data,
        original_name=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        category=cat,
        uploaded_by=uuid.UUID(current_user.id),
    )
    return APIResponse(data=FileOut.model_validate(record), message="File uploaded")


@router.get("/{file_id}")
async def download_file(
    file_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a file by ID."""
    service = FileService(db)
    record = await service.get_file(file_id, uuid.UUID(current_user.school_id))
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    # Staff see any file in their school; non-staff only their own uploads.
    assert_can_access_file(current_user, record)

    return FileResponse(
        path=record.storage_path,
        filename=record.original_name,
        media_type=record.content_type,
    )
