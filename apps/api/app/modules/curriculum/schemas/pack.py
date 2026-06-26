"""Curriculum pack schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.curriculum_pack import PackStatus


class TopicIn(BaseModel):
    title: str = Field(..., max_length=200)
    order_index: int = 0
    concepts: Optional[list[str]] = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    order_index: int
    concepts: Optional[list[str]] = None


class ChapterIn(BaseModel):
    number: Optional[str] = Field(None, max_length=20)
    title: str = Field(..., max_length=200)
    order_index: int = 0
    topics: list[TopicIn] = []


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    number: Optional[str] = None
    title: str
    order_index: int
    topics: list[TopicOut] = []


class PackCreate(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    academic_year_id: uuid.UUID
    board: str = Field(..., max_length=50)
    book_title: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=150)
    edition: Optional[str] = Field(None, max_length=50)
    blueprint: Optional[list] = None


class PackUpdate(BaseModel):
    board: Optional[str] = Field(None, max_length=50)
    book_title: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=150)
    edition: Optional[str] = Field(None, max_length=50)
    blueprint: Optional[list] = None


class PackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    class_id: uuid.UUID
    subject_id: uuid.UUID
    academic_year_id: uuid.UUID
    board: str
    book_title: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    version: int
    status: PackStatus
    blueprint: Optional[list] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None


class PackDetailOut(PackOut):
    chapters: list[ChapterOut] = []
