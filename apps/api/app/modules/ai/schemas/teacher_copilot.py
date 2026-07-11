"""Teacher Copilot API schemas."""
from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field


class CopilotLessonPlanRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    pack_id: uuid.UUID
    topic: str | None = None
    chapter: str | None = None
    scheduled_for: date | None = None


class CopilotFeedbackRequest(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID
    pack_id: uuid.UUID
    topic: str = Field(..., min_length=1, max_length=200)
    student_answer: str = Field(..., min_length=1, max_length=8000)
    rubric: str | None = Field(None, max_length=4000)


class CopilotSuggestionOut(BaseModel):
    section_title: str | None = None
    question_number: str | None = None
    issue: str | None = None
    suggestion: str | None = None
    citations: list[int] = Field(default_factory=list)
    citation_sources: list[dict] = Field(default_factory=list)


class CopilotPaperReviewOut(BaseModel):
    paper_id: uuid.UUID
    summary: str
    overall_quality: str
    suggestions: list[CopilotSuggestionOut] = Field(default_factory=list)
    grounding_sources: list[dict] = Field(default_factory=list)
    model: str | None = None


class CopilotFeedbackOut(BaseModel):
    feedback_draft: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    citations: list[int] = Field(default_factory=list)
    citation_sources: list[dict] = Field(default_factory=list)
    grounding_sources: list[dict] = Field(default_factory=list)
    tone: str = "constructive"
    model: str | None = None
