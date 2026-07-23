"""Curriculum pack schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.curriculum_pack import PackStatus


class LearningOutcomeIn(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1, max_length=1000)
    order_index: int = 0


class LearningOutcomeUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    order_index: Optional[int] = None


class LearningOutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: Optional[str] = None
    description: str
    order_index: int
    topic_id: Optional[uuid.UUID] = None
    chapter_id: Optional[uuid.UUID] = None


class TopicIn(BaseModel):
    title: str = Field(..., max_length=200)
    order_index: int = 0
    concepts: Optional[list[str]] = None
    learning_outcomes: list[LearningOutcomeIn] = []


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    order_index: Optional[int] = None
    concepts: Optional[list[str]] = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    order_index: int
    concepts: Optional[list[str]] = None
    learning_outcomes: list[LearningOutcomeOut] = []


class ChapterIn(BaseModel):
    number: Optional[str] = Field(None, max_length=20)
    title: str = Field(..., max_length=200)
    order_index: int = 0
    topics: list[TopicIn] = []
    learning_outcomes: list[LearningOutcomeIn] = []


class ChapterUpdate(BaseModel):
    number: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    order_index: Optional[int] = None


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: Optional[str] = None
    title: str
    order_index: int
    topics: list[TopicOut] = []
    learning_outcomes: list[LearningOutcomeOut] = []


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
    created_by: Optional[uuid.UUID] = None
    approved_by: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rag_indexed_at: Optional[datetime] = None
    rag_index_topic_count: Optional[int] = None
    rag_index_error: Optional[str] = None


class PackDetailOut(PackOut):
    chapters: list[ChapterOut] = []


class PackAuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pack_id: uuid.UUID
    actor_id: uuid.UUID
    actor_name: Optional[str] = None
    event_type: str
    metadata: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
