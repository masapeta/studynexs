"""File upload/download schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FileCategory(str, Enum):
    PROFILE_PHOTO = "profile_photo"
    RECEIPT_PDF = "receipt_pdf"
    DOCUMENT = "document"
    REPORT_CARD = "report_card"
    ANSWER_SHEET = "answer_sheet"


class FileOut(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    category: FileCategory
    url: str
    uploaded_by: uuid.UUID
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
