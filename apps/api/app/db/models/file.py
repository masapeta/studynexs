"""File model — uploaded file metadata."""

import enum
import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class FileCategory(str, enum.Enum):
    PROFILE_PHOTO = "profile_photo"
    RECEIPT_PDF = "receipt_pdf"
    DOCUMENT = "document"
    REPORT_CARD = "report_card"


class UploadedFile(BaseModel):
    __tablename__ = "uploaded_files"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    original_name: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[FileCategory] = mapped_column(Enum(FileCategory), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)  # Blob path
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    __table_args__ = (
        Index("ix_files_school_category", "school_id", "category"),
    )
