"""Notification schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    title: str = Field(..., max_length=200)
    body: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    link: Optional[str] = None


class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    channel: NotificationChannel
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
