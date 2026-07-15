"""Knowledge Graph schemas — curriculum spine read models."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.db.models.knowledge_graph import ConceptSource, KgEdgeType, KgNodeType


class ConceptOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    slug: str
    title: str
    order_index: int
    source: ConceptSource

    model_config = {"from_attributes": True}


class TopicSpineOut(BaseModel):
    id: uuid.UUID
    title: str
    order_index: int
    concepts: list[ConceptOut] = Field(default_factory=list)


class ChapterSpineOut(BaseModel):
    id: uuid.UUID
    number: str | None = None
    title: str
    order_index: int
    topics: list[TopicSpineOut] = Field(default_factory=list)


class SpineOut(BaseModel):
    pack_id: uuid.UUID
    subject_id: uuid.UUID
    concept_count: int
    edge_count: int
    chapters: list[ChapterSpineOut] = Field(default_factory=list)


class SpineBuildOut(BaseModel):
    pack_id: uuid.UUID
    concepts_created: int
    edges_created: int


class EdgeOut(BaseModel):
    id: uuid.UUID
    edge_type: KgEdgeType
    from_node_type: KgNodeType
    from_id: uuid.UUID
    to_node_type: KgNodeType
    to_id: uuid.UUID

    model_config = {"from_attributes": True}


class ConceptContextOut(BaseModel):
    concept: ConceptOut
    has_approved_card: bool
    concept_card_status: str | None = None
    linked_question_count: int = 0
    weak_student_count: int = 0


class StudentWeakConceptsOut(BaseModel):
    student_id: uuid.UUID
    concepts: list[ConceptOut] = Field(default_factory=list)
