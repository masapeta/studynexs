"""Student → weak Concept graph links (Batch 22).

Derived from topic mastery below threshold, mapped to spine concepts via topic title.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge, KgEdgeType, KgNodeType

logger = structlog.get_logger()

_WEAK_THRESHOLD = 70.0


class StudentWeakConceptService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _resolve_pack(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        subject_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> CurriculumPack | None:
        return (
            await self.db.execute(
                select(CurriculumPack).where(
                    CurriculumPack.school_id == school_id,
                    CurriculumPack.class_id == class_id,
                    CurriculumPack.subject_id == subject_id,
                    CurriculumPack.academic_year_id == academic_year_id,
                    CurriculumPack.status == PackStatus.APPROVED,
                )
                .order_by(CurriculumPack.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def _topic_title_map(
        self, *, school_id: uuid.UUID, pack_id: uuid.UUID
    ) -> dict[str, list[CurriculumConcept]]:
        chapters = list(
            (
                await self.db.execute(
                    select(CurriculumChapter.id).where(
                        CurriculumChapter.pack_id == pack_id,
                        CurriculumChapter.school_id == school_id,
                    )
                )
            ).scalars().all()
        )
        if not chapters:
            return {}

        topics = list(
            (
                await self.db.execute(
                    select(CurriculumTopic).where(
                        CurriculumTopic.chapter_id.in_(chapters),
                        CurriculumTopic.school_id == school_id,
                    )
                )
            ).scalars().all()
        )
        topic_ids = [t.id for t in topics]
        concepts: list[CurriculumConcept] = []
        if topic_ids:
            concepts = list(
                (
                    await self.db.execute(
                        select(CurriculumConcept).where(
                            CurriculumConcept.pack_id == pack_id,
                            CurriculumConcept.school_id == school_id,
                            CurriculumConcept.topic_id.in_(topic_ids),
                        )
                    )
                ).scalars().all()
            )

        concepts_by_topic: dict[uuid.UUID, list[CurriculumConcept]] = {}
        for concept in concepts:
            concepts_by_topic.setdefault(concept.topic_id, []).append(concept)

        out: dict[str, list[CurriculumConcept]] = {}
        for topic in topics:
            key = topic.title.strip().casefold()
            out[key] = concepts_by_topic.get(topic.id, [])
        return out

    async def sync_from_ledger(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        subject_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        ledger_rows: list[dict],
    ) -> int:
        """Rebuild STRUGGLES_WITH edges for students in this recompute pass."""
        pack = await self._resolve_pack(
            school_id=school_id,
            class_id=class_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
        )
        if pack is None:
            return 0

        student_ids = {row["student_id"] for row in ledger_rows}
        if not student_ids:
            return 0

        await self.db.execute(
            delete(KgEdge).where(
                KgEdge.school_id == school_id,
                KgEdge.pack_id == pack.id,
                KgEdge.edge_type == KgEdgeType.STRUGGLES_WITH,
                KgEdge.from_node_type == KgNodeType.STUDENT,
                KgEdge.from_id.in_(student_ids),
            )
        )

        topic_map = await self._topic_title_map(school_id=school_id, pack_id=pack.id)
        edges_created = 0

        for row in ledger_rows:
            mastery = float(row["mastery_pct"])
            if mastery >= _WEAK_THRESHOLD:
                continue
            topic_key = str(row.get("topic_display") or row["topic"]).strip().casefold()
            concepts = topic_map.get(topic_key, [])
            if not concepts:
                continue
            for concept in concepts:
                edge = KgEdge(
                    school_id=school_id,
                    pack_id=pack.id,
                    edge_type=KgEdgeType.STRUGGLES_WITH,
                    from_node_type=KgNodeType.STUDENT,
                    from_id=row["student_id"],
                    to_node_type=KgNodeType.CONCEPT,
                    to_id=concept.id,
                    metadata_={
                        "mastery_pct": mastery,
                        "topic": row.get("topic_display") or row["topic"],
                        "subject_id": str(subject_id),
                    },
                )
                self.db.add(edge)
                edges_created += 1

        await self.db.flush()
        logger.info(
            "student_weak_concepts_synced",
            school_id=str(school_id),
            pack_id=str(pack.id),
            edges=edges_created,
        )
        return edges_created

    async def get_weak_concepts_for_student(
        self,
        *,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_id: uuid.UUID | None = None,
        pack_id: uuid.UUID | None = None,
    ) -> list[tuple[CurriculumConcept, dict | None]]:
        filters = [
            KgEdge.school_id == school_id,
            KgEdge.edge_type == KgEdgeType.STRUGGLES_WITH,
            KgEdge.from_node_type == KgNodeType.STUDENT,
            KgEdge.from_id == student_id,
        ]
        if pack_id is not None:
            filters.append(KgEdge.pack_id == pack_id)

        rows = list(
            (
                await self.db.execute(
                    select(KgEdge).where(*filters).order_by(KgEdge.created_at.desc())
                )
            ).scalars().all()
        )
        if not rows:
            return []

        concept_ids = [e.to_id for e in rows]
        concepts = list(
            (
                await self.db.execute(
                    select(CurriculumConcept).where(
                        CurriculumConcept.school_id == school_id,
                        CurriculumConcept.id.in_(concept_ids),
                    )
                )
            ).scalars().all()
        )
        by_id = {c.id: c for c in concepts}
        out: list[tuple[CurriculumConcept, dict | None]] = []
        for edge in rows:
            concept = by_id.get(edge.to_id)
            if concept is None:
                continue
            if subject_id is not None:
                meta = edge.metadata_ or {}
                if meta.get("subject_id") and meta["subject_id"] != str(subject_id):
                    continue
            out.append((concept, edge.metadata_))
        return out
