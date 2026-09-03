"""File service — upload/download with local or Azure Blob storage."""

import os
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.file import FileCategory, UploadedFile

settings = get_settings()

# Local upload directory (dev) — in production, use Azure Blob
UPLOAD_DIR = Path(settings.FILE_UPLOAD_DIR if hasattr(settings, 'FILE_UPLOAD_DIR') else "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class FileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(
        self,
        school_id: uuid.UUID,
        file_data: bytes,
        original_name: str,
        content_type: str,
        category: FileCategory,
        uploaded_by: uuid.UUID,
    ) -> UploadedFile:
        """Save file to local storage (dev) or Azure Blob (prod)."""
        file_id = uuid.uuid4()
        ext = Path(original_name).suffix
        filename = f"{file_id}{ext}"
        storage_path = str(UPLOAD_DIR / str(school_id) / filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        # Write to disk (in prod: upload to Azure Blob)
        with open(storage_path, "wb") as f:
            f.write(file_data)

        url = f"/api/v1/files/{file_id}"

        record = UploadedFile(
            id=file_id,
            school_id=school_id,
            filename=filename,
            original_name=original_name,
            content_type=content_type,
            size_bytes=len(file_data),
            category=category,
            storage_path=storage_path,
            url=url,
            uploaded_by=uploaded_by,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_file(
        self, file_id: uuid.UUID, school_id: uuid.UUID | None = None
    ) -> UploadedFile | None:
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        if school_id is not None:
            query = query.where(UploadedFile.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_files(
        self, school_id: uuid.UUID, category: FileCategory | None = None
    ) -> list[UploadedFile]:
        query = select(UploadedFile).where(UploadedFile.school_id == school_id)
        if category:
            query = query.where(UploadedFile.category == category)
        result = await self.db.execute(query.order_by(UploadedFile.created_at.desc()).limit(50))
        return list(result.scalars().all())
