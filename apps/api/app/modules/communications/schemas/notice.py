"""Communication schemas — notices."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.communication import NoticePriority
from app.db.models.communication import NoticeAudience


_STAFF_ROLES = frozenset({"admin", "super_admin", "class_incharge", "teacher", "operations"})
_EXTERNAL_ROLES = frozenset({"student", "parent"})


class NoticeCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    audience: NoticeAudience = NoticeAudience.EXTERNAL
    target_roles: list[str]
    priority: NoticePriority = NoticePriority.MEDIUM
    expires_at: Optional[datetime] = None
    class_id: Optional[uuid.UUID] = None


class NoticeOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    audience: NoticeAudience
    target_roles: list[str]
    priority: NoticePriority
    created_by: uuid.UUID
    class_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
