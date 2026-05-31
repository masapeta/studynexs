"""School operations schemas — library, events."""

import uuid
from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LibraryBookOut(BaseModel):
    id: uuid.UUID
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    total_copies: int
    available_copies: int
    model_config = ConfigDict(from_attributes=True)

class LibraryBookCreate(BaseModel):
    title: str = Field(..., max_length=300)
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    total_copies: int = 1

class EventOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    event_date: date
    event_time: Optional[str] = None
    venue: Optional[str] = None
    target_roles: Optional[list[str]] = None
    model_config = ConfigDict(from_attributes=True)

class EventCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    event_date: date
    venue: Optional[str] = None
    target_roles: Optional[list[str]] = None
