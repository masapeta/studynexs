"""Knowledge Graph models — curriculum spine (Batch 17).

Typed concept nodes + queryable edges derived from approved CurriculumPacks.
Postgres adjacency (not a separate graph DB) per CLAUDE.md §39.3.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class ConceptSource(str, enum.Enum):
    PACK_JSONB = "pack_jsonb"
    MANUAL = "manual"


class KgNodeType(str, enum.Enum):
    PACK = "pack"
    SUBJECT = "subject"
    CHAPTER = "chapter"
    TOPIC = "topic"
    CONCEPT = "concept"
    QUESTION_BANK_ITEM = "question_bank_item"
    STUDENT = "student"


class KgEdgeType(str, enum.Enum):
    CONTAINS = "contains"
    PART_OF = "part_of"
    TESTS = "tests"
    STRUGGLES_WITH = "struggles_with"


class CurriculumConcept(BaseModel):
    """First-class concept node promoted from topic JSONB on pack approval."""

    __tablename__ = "curriculum_concepts"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_topics.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[ConceptSource] = mapped_column(
        Enum(ConceptSource), nullable=False, default=ConceptSource.PACK_JSONB
    )

    __table_args__ = (
        UniqueConstraint("school_id", "topic_id", "slug", name="uq_concept_topic_slug"),
        Index("ix_concepts_school_pack", "school_id", "pack_id"),
        Index("ix_concepts_topic", "topic_id"),
    )


class KgEdge(BaseModel):
    """Tenant-scoped relationship between spine entities."""

    __tablename__ = "kg_edges"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("curriculum_packs.id", ondelete="CASCADE"), nullable=True
    )
    edge_type: Mapped[KgEdgeType] = mapped_column(Enum(KgEdgeType), nullable=False)
    from_node_type: Mapped[KgNodeType] = mapped_column(Enum(KgNodeType), nullable=False)
    from_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_node_type: Mapped[KgNodeType] = mapped_column(Enum(KgNodeType), nullable=False)
    to_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "edge_type",
            "from_node_type",
            "from_id",
            "to_node_type",
            "to_id",
            name="uq_kg_edge_endpoints",
        ),
        Index("ix_kg_edges_school_pack", "school_id", "pack_id"),
        Index("ix_kg_edges_to", "school_id", "to_node_type", "to_id"),
        Index("ix_kg_edges_from", "school_id", "from_node_type", "from_id"),
    )
