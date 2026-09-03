"""Knowledge Graph service — build and query the curriculum spine (Batch 17)."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import (
    ConceptSource,
    CurriculumConcept,
    KgEdge,
    KgEdgeType,
    KgNodeType,
)
from app.modules.curriculum.services.pack_service import PackService
from app.modules.knowledge_graph.schemas.graph import (
    ChapterSpineOut,
    ConceptOut,
    SpineOut,
    TopicSpineOut,
)

logger = structlog.get_logger()

_SLUG_RE = re.compile(r"[^\w\s-]", re.UNICODE)
_SPINE_EDGE_TYPES = (KgEdgeType.CONTAINS, KgEdgeType.PART_OF)


class KnowledgeGraphError(ValueError):
    """Graph cannot be built or queried."""


@dataclass
class SpineBuildResult:
    pack_id: uuid.UUID
    concepts_created: int
    edges_created: int


def concept_slug(label: str) -> str:
    """Normalize a concept label to a stable slug within a topic."""
    cleaned = _SLUG_RE.sub("", label.strip().lower())
    slug = re.sub(r"[\s_]+", "-", cleaned).strip("-")
    return (slug[:120] or "concept")


class KnowledgeGraphService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.packs = PackService(db)

    async def delete_spine_for_pack(self, *, school_id: uuid.UUID, pack_id: uuid.UUID) -> None:
        await self.db.execute(
            delete(KgEdge).where(
                KgEdge.school_id == school_id,
                KgEdge.pack_id == pack_id,
                KgEdge.edge_type.in_(_SPINE_EDGE_TYPES),
            )
        )
        await self.db.execute(
            delete(CurriculumConcept).where(
                CurriculumConcept.school_id == school_id,
                CurriculumConcept.pack_id == pack_id,
            )
        )

    async def _add_edge(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        edge_type: KgEdgeType,
        from_node_type: KgNodeType,
        from_id: uuid.UUID,
        to_node_type: KgNodeType,
        to_id: uuid.UUID,
        metadata: dict | None = None,
    ) -> KgEdge:
        edge = KgEdge(
            school_id=school_id,
            pack_id=pack_id,
            edge_type=edge_type,
            from_node_type=from_node_type,
            from_id=from_id,
            to_node_type=to_node_type,
            to_id=to_id,
            metadata_=metadata,
        )
        self.db.add(edge)
        return edge

    async def _snapshot_tests_links(
        self, *, school_id: uuid.UUID, pack_id: uuid.UUID
    ) -> list[tuple[uuid.UUID, uuid.UUID, uuid.UUID, str]]:
        """Capture TESTS edge targets before spine rebuild replaces concept ids."""
        rows = await self.db.execute(
            select(
                KgEdge.id,
                KgEdge.from_id,
                CurriculumConcept.topic_id,
                CurriculumConcept.slug,
            )
            .join(CurriculumConcept, KgEdge.to_id == CurriculumConcept.id)
            .where(
                KgEdge.school_id == school_id,
                KgEdge.pack_id == pack_id,
                KgEdge.edge_type == KgEdgeType.TESTS,
            )
        )
        return list(rows.all())

    async def _remap_tests_links(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        snapshots: list[tuple[uuid.UUID, uuid.UUID, uuid.UUID, str]],
    ) -> None:
        if not snapshots:
            return
        concepts = list(
            (
                await self.db.execute(
                    select(CurriculumConcept).where(
                        CurriculumConcept.school_id == school_id,
                        CurriculumConcept.pack_id == pack_id,
                    )
                )
            ).scalars().all()
        )
        by_topic_slug = {(c.topic_id, c.slug): c.id for c in concepts}
        for edge_id, _from_id, topic_id, slug in snapshots:
            new_concept_id = by_topic_slug.get((topic_id, slug))
            if new_concept_id is None:
                await self.db.execute(delete(KgEdge).where(KgEdge.id == edge_id))
            else:
                await self.db.execute(
                    update(KgEdge)
                    .where(KgEdge.id == edge_id)
                    .values(to_id=new_concept_id)
                )

    async def build_spine_from_pack(
        self, *, school_id: uuid.UUID, pack_id: uuid.UUID
    ) -> SpineBuildResult:
        """Idempotent: rebuild spine edges + concept nodes from pack hierarchy."""
        pack = await self.packs.get_pack(school_id, pack_id)
        if pack.status != PackStatus.APPROVED:
            raise KnowledgeGraphError("Spine can only be built from approved packs")

        tests_snapshots = await self._snapshot_tests_links(
            school_id=school_id, pack_id=pack_id
        )
        await self.delete_spine_for_pack(school_id=school_id, pack_id=pack_id)

        chapters = list(
            (
                await self.db.execute(
                    select(CurriculumChapter)
                    .where(
                        CurriculumChapter.pack_id == pack_id,
                        CurriculumChapter.school_id == school_id,
                    )
                    .order_by(CurriculumChapter.order_index)
                )
            ).scalars().all()
        )
        if not chapters:
            raise KnowledgeGraphError("Pack has no chapters — cannot build spine")

        chapter_ids = [c.id for c in chapters]
        topics = list(
            (
                await self.db.execute(
                    select(CurriculumTopic)
                    .where(
                        CurriculumTopic.chapter_id.in_(chapter_ids),
                        CurriculumTopic.school_id == school_id,
                    )
                    .order_by(CurriculumTopic.order_index)
                )
            ).scalars().all()
        )
        topics_by_chapter: dict[uuid.UUID, list[CurriculumTopic]] = {}
        for topic in topics:
            topics_by_chapter.setdefault(topic.chapter_id, []).append(topic)

        concepts_created = 0
        edges_created = 0

        await self._add_edge(
            school_id=school_id,
            pack_id=pack_id,
            edge_type=KgEdgeType.PART_OF,
            from_node_type=KgNodeType.PACK,
            from_id=pack.id,
            to_node_type=KgNodeType.SUBJECT,
            to_id=pack.subject_id,
            metadata={"board": pack.board},
        )
        edges_created += 1

        for chapter in chapters:
            await self._add_edge(
                school_id=school_id,
                pack_id=pack_id,
                edge_type=KgEdgeType.CONTAINS,
                from_node_type=KgNodeType.PACK,
                from_id=pack.id,
                to_node_type=KgNodeType.CHAPTER,
                to_id=chapter.id,
            )
            edges_created += 1

            for topic in topics_by_chapter.get(chapter.id, []):
                await self._add_edge(
                    school_id=school_id,
                    pack_id=pack_id,
                    edge_type=KgEdgeType.CONTAINS,
                    from_node_type=KgNodeType.CHAPTER,
                    from_id=chapter.id,
                    to_node_type=KgNodeType.TOPIC,
                    to_id=topic.id,
                )
                edges_created += 1

                raw_concepts = topic.concepts or []
                for idx, label in enumerate(raw_concepts):
                    text = str(label).strip()
                    if not text:
                        continue
                    slug = concept_slug(text)
                    concept = CurriculumConcept(
                        school_id=school_id,
                        pack_id=pack_id,
                        topic_id=topic.id,
                        slug=slug,
                        title=text[:200],
                        order_index=idx,
                        source=ConceptSource.PACK_JSONB,
                    )
                    self.db.add(concept)
                    await self.db.flush()
                    concepts_created += 1

                    await self._add_edge(
                        school_id=school_id,
                        pack_id=pack_id,
                        edge_type=KgEdgeType.CONTAINS,
                        from_node_type=KgNodeType.TOPIC,
                        from_id=topic.id,
                        to_node_type=KgNodeType.CONCEPT,
                        to_id=concept.id,
                        metadata={"title": concept.title, "slug": concept.slug},
                    )
                    edges_created += 1

        await self.db.flush()
        await self._remap_tests_links(
            school_id=school_id, pack_id=pack_id, snapshots=tests_snapshots
        )
        logger.info(
            "kg_spine_built",
            school_id=str(school_id),
            pack_id=str(pack_id),
            concepts=concepts_created,
            edges=edges_created,
        )
        return SpineBuildResult(
            pack_id=pack_id,
            concepts_created=concepts_created,
            edges_created=edges_created,
        )

    async def get_spine(self, *, school_id: uuid.UUID, pack_id: uuid.UUID) -> SpineOut:
        pack = await self.packs.get_pack(school_id, pack_id)

        chapters = list(
            (
                await self.db.execute(
                    select(CurriculumChapter)
                    .where(
                        CurriculumChapter.pack_id == pack_id,
                        CurriculumChapter.school_id == school_id,
                    )
                    .order_by(CurriculumChapter.order_index)
                )
            ).scalars().all()
        )
        chapter_ids = [c.id for c in chapters]
        topics = []
        if chapter_ids:
            topics = list(
                (
                    await self.db.execute(
                        select(CurriculumTopic)
                        .where(
                            CurriculumTopic.chapter_id.in_(chapter_ids),
                            CurriculumTopic.school_id == school_id,
                        )
                        .order_by(CurriculumTopic.order_index)
                    )
                ).scalars().all()
            )

        concepts = list(
            (
                await self.db.execute(
                    select(CurriculumConcept)
                    .where(
                        CurriculumConcept.pack_id == pack_id,
                        CurriculumConcept.school_id == school_id,
                    )
                    .order_by(CurriculumConcept.order_index)
                )
            ).scalars().all()
        )
        concepts_by_topic: dict[uuid.UUID, list[CurriculumConcept]] = {}
        for concept in concepts:
            concepts_by_topic.setdefault(concept.topic_id, []).append(concept)

        topics_by_chapter: dict[uuid.UUID, list[CurriculumTopic]] = {}
        for topic in topics:
            topics_by_chapter.setdefault(topic.chapter_id, []).append(topic)

        from sqlalchemy import func

        edge_count = (
            await self.db.scalar(
                select(func.count())
                .select_from(KgEdge)
                .where(KgEdge.school_id == school_id, KgEdge.pack_id == pack_id)
            )
        ) or 0

        chapter_out: list[ChapterSpineOut] = []
        for chapter in chapters:
            topic_out: list[TopicSpineOut] = []
            for topic in topics_by_chapter.get(chapter.id, []):
                topic_out.append(
                    TopicSpineOut(
                        id=topic.id,
                        title=topic.title,
                        order_index=topic.order_index,
                        concepts=[
                            ConceptOut.model_validate(c)
                            for c in concepts_by_topic.get(topic.id, [])
                        ],
                    )
                )
            chapter_out.append(
                ChapterSpineOut(
                    id=chapter.id,
                    number=chapter.number,
                    title=chapter.title,
                    order_index=chapter.order_index,
                    topics=topic_out,
                )
            )

        return SpineOut(
            pack_id=pack.id,
            subject_id=pack.subject_id,
            concept_count=len(concepts),
            edge_count=int(edge_count),
            chapters=chapter_out,
        )

    async def backfill_approved_packs(self, *, school_id: uuid.UUID) -> int:
        """Build spine for all approved packs missing graph data (tenant-scoped)."""
        packs = list(
            (
                await self.db.execute(
                    select(CurriculumPack).where(
                        CurriculumPack.school_id == school_id,
                        CurriculumPack.status == PackStatus.APPROVED,
                    )
                )
            ).scalars().all()
        )
        built = 0
        for pack in packs:
            has_edges = await self.db.scalar(
                select(KgEdge.id)
                .where(KgEdge.school_id == school_id, KgEdge.pack_id == pack.id)
                .limit(1)
            )
            if has_edges:
                continue
            await self.build_spine_from_pack(school_id=school_id, pack_id=pack.id)
            built += 1
        return built
