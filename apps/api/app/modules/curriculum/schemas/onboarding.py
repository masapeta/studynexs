"""Academic onboarding schemas — Stage 2A."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.modules.curriculum.schemas.pack import PackDetailOut


class CurriculumInputType(str, Enum):
    TOC = "toc"
    SYLLABUS = "syllabus"
    CHAPTER_LIST = "chapter_list"
    FREE_TEXT = "free_text"


class OnboardingProposeRequest(BaseModel):
    """Admin/HOD inputs for AI-assisted draft pack creation."""

    class_id: uuid.UUID
    subject_id: uuid.UUID
    academic_year_id: uuid.UUID
    board: str = Field(..., max_length=50)
    book_title: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=150)
    edition: Optional[str] = Field(None, max_length=50)
    input_type: CurriculumInputType = CurriculumInputType.CHAPTER_LIST
    curriculum_text: Optional[str] = Field(None, max_length=50000)
    file_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def require_curriculum_source(self) -> "OnboardingProposeRequest":
        if not (self.curriculum_text or "").strip() and self.file_id is None:
            raise ValueError("Provide curriculum_text or file_id for AI extraction")
        return self


class ExtractionChapterOut(BaseModel):
    number: Optional[str] = None
    title: str
    topics: list[str] = []
    learning_outcomes: list[str] = []


class OnboardingProposeResponse(BaseModel):
    pack: PackDetailOut
    extraction_source: str
    chapters_proposed: int
    topics_proposed: int
    low_confidence_notes: list[str] = []
    credits_used: int = 0


class IntelligencePhase(str, Enum):
    DRAFT = "draft"
    APPROVED_PREPARING = "approved_preparing"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"


class AcademicIntelligenceStatusOut(BaseModel):
    pack_id: uuid.UUID
    phase: IntelligencePhase
    pack_status: str
    pack_approved: bool
    kg_ready: bool
    rag_ready: bool
    academic_intelligence_ready: bool
    message: str
    rag_index_error: Optional[str] = None
    retrievable_topic_count: int = 0
    rag_vector_count: int = 0
    can_approve: bool = False
    approval_blockers: list[str] = Field(default_factory=list)
