"""Communication schemas — notices."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.communication import NoticePriority


class NoticeCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    target_roles: list[str]  # ["student", "parent", "teacher"]
    priority: NoticePriority = NoticePriority.MEDIUM
    expires_at: Optional[datetime] = None


class NoticeOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    target_roles: list[str]
    priority: NoticePriority
    created_by: uuid.UUID
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
