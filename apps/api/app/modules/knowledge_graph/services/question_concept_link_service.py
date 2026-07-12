"""Question → Concept graph links (Batch 19).

Links approved QuestionBankItem rows to CurriculumConcept nodes via kg_edges (TESTS).
Resolution uses grounded paper citations + per-question concept labels.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import CurriculumChapter, CurriculumTopic
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge, KgEdgeType, KgNodeType
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import QuestionPaper
from app.modules.ai.services.assessment_grounding import resolve_citations
from app.modules.knowledge_graph.services.graph_service import concept_slug

logger = structlog.get_logger()

_SPINE_EDGE_TYPES = (KgEdgeType.CONTAINS, KgEdgeType.PART_OF)


@dataclass
class LinkBuildResult:
    paper_id: uuid.UUID
    items_linked: int
    edges_created: int


class QuestionConceptLinkService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def delete_links_for_paper(
        self, *, school_id: uuid.UUID, paper_id: uuid.UUID
    ) -> int:
        """Remove TESTS edges for all bank items sourced from this paper."""
        item_ids = list(
            (
                await self.db.execute(
                    select(QuestionBankItem.id).where(
                        QuestionBankItem.school_id == school_id,
                        QuestionBankItem.source_paper_id == paper_id,
                    )
                )
            ).scalars().all()
        )
        if not item_ids:
            return 0
        result = await self.db.execute(
            delete(KgEdge).where(
                KgEdge.school_id == school_id,
                KgEdge.edge_type == KgEdgeType.TESTS,
                KgEdge.from_node_type == KgNodeType.QUESTION_BANK_ITEM,
                KgEdge.from_id.in_(item_ids),
            )
        )
        return int(result.rowcount or 0)

    async def _resolve_topic_ids(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        grounding_sources: list[dict],
        citation_indices: list[int],
    ) -> list[uuid.UUID]:
        sources = resolve_citations(grounding_sources, citation_indices)
        topic_ids: list[uuid.UUID] = []
        titles: list[str] = []

        for src in sources:
            ref = src.get("ref_id")
            if ref:
                try:
                    topic_ids.append(uuid.UUID(str(ref)))
                    continue
                except ValueError:
                    pass
            topic = str(src.get("topic") or "").strip()
            if topic:
                titles.append(topic)

        if titles:
            rows = await self.db.execute(
                select(CurriculumTopic.id)
                .join(CurriculumChapter, CurriculumChapter.id == CurriculumTopic.chapter_id)
                .where(
                    CurriculumTopic.school_id == school_id,
                    CurriculumChapter.pack_id == pack_id,
                    CurriculumTopic.title.in_(titles),
                )
            )
            for tid in rows.scalars().all():
                if tid not in topic_ids:
                    topic_ids.append(tid)

        return topic_ids

    async def resolve_concept_ids(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        grounding_sources: list[dict] | None,
        question: dict,
    ) -> list[uuid.UUID]:
        """Map a paper question to spine concept UUIDs."""
        raw_labels = question.get("concepts") or []
        label_slugs = {concept_slug(str(label)) for label in raw_labels if str(label).strip()}

        topic_ids: list[uuid.UUID] = []
        citations = question.get("citations")
        if isinstance(citations, list) and grounding_sources:
            topic_ids = await self._resolve_topic_ids(
                school_id=school_id,
                pack_id=pack_id,
                grounding_sources=grounding_sources,
                citation_indices=[int(c) for c in citations],
            )

        topic_concepts: list[CurriculumConcept] = []
        if topic_ids:
            topic_concepts = list(
                (
                    await self.db.execute(
                        select(CurriculumConcept).where(
                            CurriculumConcept.school_id == school_id,
                            CurriculumConcept.pack_id == pack_id,
                            CurriculumConcept.topic_id.in_(topic_ids),
                        )
                    )
                ).scalars().all()
            )

        if topic_concepts and label_slugs:
            matched = [c for c in topic_concepts if c.slug in label_slugs]
            if matched:
                return [c.id for c in matched]

        if topic_concepts:
            return [c.id for c in topic_concepts]

        if label_slugs:
            rows = list(
                (
                    await self.db.execute(
                        select(CurriculumConcept).where(
                            CurriculumConcept.school_id == school_id,
                            CurriculumConcept.pack_id == pack_id,
                            CurriculumConcept.slug.in_(label_slugs),
                        )
                    )
                ).scalars().all()
            )
            return [c.id for c in rows]

        return []

    async def _add_tests_edge(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        item_id: uuid.UUID,
        concept_id: uuid.UUID,
        metadata: dict | None = None,
    ) -> KgEdge | None:
        existing = (
            await self.db.execute(
                select(KgEdge.id).where(
                    KgEdge.school_id == school_id,
                    KgEdge.edge_type == KgEdgeType.TESTS,
                    KgEdge.from_node_type == KgNodeType.QUESTION_BANK_ITEM,
                    KgEdge.from_id == item_id,
                    KgEdge.to_node_type == KgNodeType.CONCEPT,
                    KgEdge.to_id == concept_id,
                )
            )
        ).scalar_one_or_none()
        if existing:
            return None

        edge = KgEdge(
            school_id=school_id,
            pack_id=pack_id,
            edge_type=KgEdgeType.TESTS,
            from_node_type=KgNodeType.QUESTION_BANK_ITEM,
            from_id=item_id,
            to_node_type=KgNodeType.CONCEPT,
            to_id=concept_id,
            metadata_=metadata,
        )
        self.db.add(edge)
        return edge

    async def link_items_from_paper(
        self,
        paper: QuestionPaper,
        items: list[QuestionBankItem],
        *,
        questions_by_key: dict[tuple[str, str], dict],
    ) -> LinkBuildResult:
        """Create TESTS edges for bank items ingested from a grounded paper."""
        if not paper.grounded or not paper.pack_id:
            return LinkBuildResult(paper_id=paper.id, items_linked=0, edges_created=0)

        pack_id = paper.pack_id
        sources = list(paper.grounding_sources or [])
        items_linked = 0
        edges_created = 0

        for item in items:
            question = questions_by_key.get((item.section_title, item.question_number))
            if question is None:
                continue

            concept_ids = await self.resolve_concept_ids(
                school_id=paper.school_id,
                pack_id=pack_id,
                grounding_sources=sources,
                question=question,
            )
            if not concept_ids:
                continue

            items_linked += 1
            for concept_id in concept_ids:
                meta = {
                    "source_paper_id": str(paper.id),
                    "section_title": item.section_title,
                    "question_number": item.question_number,
                }
                edge = await self._add_tests_edge(
                    school_id=paper.school_id,
                    pack_id=pack_id,
                    item_id=item.id,
                    concept_id=concept_id,
                    metadata=meta,
                )
                if edge is not None:
                    edges_created += 1

        await self.db.flush()
        logger.info(
            "question_concept_links_built",
            paper_id=str(paper.id),
            items_linked=items_linked,
            edges_created=edges_created,
        )
        return LinkBuildResult(
            paper_id=paper.id,
            items_linked=items_linked,
            edges_created=edges_created,
        )

    async def get_concepts_for_item(
        self, *, school_id: uuid.UUID, item_id: uuid.UUID
    ) -> list[CurriculumConcept]:
        """Concepts linked to a question bank item (tenant-scoped)."""
        item = (
            await self.db.execute(
                select(QuestionBankItem).where(
                    QuestionBankItem.id == item_id,
                    QuestionBankItem.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if item is None:
            return []

        edges = list(
            (
                await self.db.execute(
                    select(KgEdge.to_id).where(
                        KgEdge.school_id == school_id,
                        KgEdge.edge_type == KgEdgeType.TESTS,
                        KgEdge.from_node_type == KgNodeType.QUESTION_BANK_ITEM,
                        KgEdge.from_id == item_id,
                    )
                )
            ).scalars().all()
        )
        if not edges:
            return []

        return list(
            (
                await self.db.execute(
                    select(CurriculumConcept)
                    .where(
                        CurriculumConcept.school_id == school_id,
                        CurriculumConcept.id.in_(edges),
                    )
                    .order_by(CurriculumConcept.order_index)
                )
            ).scalars().all()
        )
