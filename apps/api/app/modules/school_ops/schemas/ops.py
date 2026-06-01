"""School operations schemas — library, events."""

import uuid
from datetime import date
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


class TransportRouteCreate(BaseModel):
    route_name: str = Field(..., max_length=100)
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_contact: Optional[str] = None
    stops: Optional[list] = None


class TransportAssignRequest(BaseModel):
    student_id: uuid.UUID
    route_id: uuid.UUID
    boarding_stop: Optional[str] = None


class ResidentialBlockCreate(BaseModel):
    block_name: str = Field(..., max_length=100)
    block_gender: str = "mixed"
    warden_name: Optional[str] = None
    warden_contact: Optional[str] = None
    total_rooms: int = 0


class ResidentialAllocateRequest(BaseModel):
    student_id: uuid.UUID
    block_id: uuid.UUID
    room_number: Optional[str] = None
