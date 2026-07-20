"""Curriculum pack service — create/build draft, approve to immutable, version."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.modules.curriculum.schemas.pack import (
    ChapterIn,
    LearningOutcomeIn,
    LearningOutcomeUpdate,
    PackCreate,
    PackUpdate,
    TopicIn,
)
from app.modules.curriculum.services.pack_audit import PackAuditEventType, record_pack_audit_event

if TYPE_CHECKING:
    from app.modules.ai.rag.service import RagService

logger = structlog.get_logger()


class PackError(ValueError):
    """Pack cannot be created or modified."""


class PackService:
    def __init__(self, db: AsyncSession, *, rag: "RagService | None" = None):
        self.db = db
        self._rag = rag

    async def create_pack(
        self, school_id: uuid.UUID, data: PackCreate, created_by: uuid.UUID
    ) -> CurriculumPack:
        scope = TenantScope(self.db, school_id)
        await scope.subject_in_class(data.subject_id, data.class_id)
        await scope.academic_year(data.academic_year_id)

        max_version = await self.db.scalar(
            select(func.max(CurriculumPack.version)).where(
                CurriculumPack.school_id == school_id,
                CurriculumPack.class_id == data.class_id,
                CurriculumPack.subject_id == data.subject_id,
                CurriculumPack.academic_year_id == data.academic_year_id,
            )
        )
        pack = CurriculumPack(
            school_id=school_id,
            class_id=data.class_id,
            subject_id=data.subject_id,
            academic_year_id=data.academic_year_id,
            board=data.board,
            book_title=data.book_title,
            publisher=data.publisher,
            edition=data.edition,
            blueprint=data.blueprint,
            version=(max_version or 0) + 1,
            status=PackStatus.DRAFT,
            created_by=created_by,
        )
        self.db.add(pack)
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=created_by,
            event_type=PackAuditEventType.PACK_CREATED,
            metadata={
                "version": pack.version,
                "board": pack.board,
                "class_id": str(pack.class_id),
                "subject_id": str(pack.subject_id),
                "academic_year_id": str(pack.academic_year_id),
            },
        )
        return pack

    async def get_pack(self, school_id: uuid.UUID, pack_id: uuid.UUID) -> CurriculumPack:
        pack = (
            await self.db.execute(
                select(CurriculumPack).where(
                    CurriculumPack.id == pack_id, CurriculumPack.school_id == school_id
                )
            )
        ).scalar_one_or_none()
        if not pack:
            raise PackError("Curriculum pack not found")
        return pack

    async def _require_draft(self, pack: CurriculumPack) -> None:
        if pack.status != PackStatus.DRAFT:
            raise PackError("Approved packs are immutable — create a new version to change them")

    async def list_packs(
        self,
        school_id: uuid.UUID,
        *,
        class_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
    ) -> list[CurriculumPack]:
        query = select(CurriculumPack).where(CurriculumPack.school_id == school_id)
        if class_id:
            query = query.where(CurriculumPack.class_id == class_id)
        if subject_id:
            query = query.where(CurriculumPack.subject_id == subject_id)
        query = query.order_by(CurriculumPack.created_at.desc())
        return list((await self.db.execute(query)).scalars().all())

    async def get_chapters(self, pack_id: uuid.UUID) -> list[CurriculumChapter]:
        return list(
            (
                await self.db.execute(
                    select(CurriculumChapter)
                    .where(CurriculumChapter.pack_id == pack_id)
                    .order_by(CurriculumChapter.order_index, CurriculumChapter.created_at)
                )
            ).scalars().all()
        )

    async def get_topics_for_chapters(
        self, chapter_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[CurriculumTopic]]:
        if not chapter_ids:
            return {}
        rows = (
            await self.db.execute(
                select(CurriculumTopic)
                .where(CurriculumTopic.chapter_id.in_(chapter_ids))
                .order_by(CurriculumTopic.order_index, CurriculumTopic.created_at)
            )
        ).scalars().all()
        out: dict[uuid.UUID, list[CurriculumTopic]] = {}
        for t in rows:
            out.setdefault(t.chapter_id, []).append(t)
        return out

    async def get_outcomes_for_topics(
        self, topic_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[CurriculumLearningOutcome]]:
        if not topic_ids:
            return {}
        rows = (
            await self.db.execute(
                select(CurriculumLearningOutcome)
                .where(CurriculumLearningOutcome.topic_id.in_(topic_ids))
                .order_by(
                    CurriculumLearningOutcome.order_index,
                    CurriculumLearningOutcome.created_at,
                )
            )
        ).scalars().all()
        out: dict[uuid.UUID, list[CurriculumLearningOutcome]] = {}
        for lo in rows:
            assert lo.topic_id is not None
            out.setdefault(lo.topic_id, []).append(lo)
        return out

    async def get_outcomes_for_chapters(
        self, chapter_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[CurriculumLearningOutcome]]:
        if not chapter_ids:
            return {}
        rows = (
            await self.db.execute(
                select(CurriculumLearningOutcome)
                .where(CurriculumLearningOutcome.chapter_id.in_(chapter_ids))
                .order_by(
                    CurriculumLearningOutcome.order_index,
                    CurriculumLearningOutcome.created_at,
                )
            )
        ).scalars().all()
        out: dict[uuid.UUID, list[CurriculumLearningOutcome]] = {}
        for lo in rows:
            assert lo.chapter_id is not None
            out.setdefault(lo.chapter_id, []).append(lo)
        return out

    async def _add_outcomes_to_topic(
        self,
        *,
        school_id: uuid.UUID,
        topic_id: uuid.UUID,
        outcomes: list[LearningOutcomeIn],
    ) -> None:
        for lo in outcomes:
            self.db.add(
                CurriculumLearningOutcome(
                    school_id=school_id,
                    topic_id=topic_id,
                    code=lo.code,
                    description=lo.description,
                    order_index=lo.order_index,
                )
            )

    async def _add_outcomes_to_chapter(
        self,
        *,
        school_id: uuid.UUID,
        chapter_id: uuid.UUID,
        outcomes: list[LearningOutcomeIn],
    ) -> None:
        for lo in outcomes:
            self.db.add(
                CurriculumLearningOutcome(
                    school_id=school_id,
                    chapter_id=chapter_id,
                    code=lo.code,
                    description=lo.description,
                    order_index=lo.order_index,
                )
            )

    async def update_pack(
        self,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        data: PackUpdate,
        *,
        actor_id: uuid.UUID,
    ) -> CurriculumPack:
        pack = await self.get_pack(school_id, pack_id)
        await self._require_draft(pack)
        changed = list(data.model_dump(exclude_unset=True).keys())
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pack, field, value)
        await self.db.flush()
        if changed:
            await record_pack_audit_event(
                self.db,
                school_id=school_id,
                pack_id=pack.id,
                actor_id=actor_id,
                event_type=PackAuditEventType.PACK_UPDATED,
                metadata={"fields": changed},
            )
        return pack

    async def add_chapter(
        self,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        data: ChapterIn,
        *,
        actor_id: uuid.UUID,
    ) -> CurriculumChapter:
        pack = await self.get_pack(school_id, pack_id)
        await self._require_draft(pack)
        chapter = CurriculumChapter(
            school_id=school_id,
            pack_id=pack.id,
            number=data.number,
            title=data.title,
            order_index=data.order_index,
        )
        self.db.add(chapter)
        await self.db.flush()
        for t in data.topics:
            topic = CurriculumTopic(
                school_id=school_id,
                chapter_id=chapter.id,
                title=t.title,
                order_index=t.order_index,
                concepts=t.concepts,
            )
            self.db.add(topic)
            await self.db.flush()
            await self._add_outcomes_to_topic(
                school_id=school_id, topic_id=topic.id, outcomes=t.learning_outcomes
            )
        await self._add_outcomes_to_chapter(
            school_id=school_id, chapter_id=chapter.id, outcomes=data.learning_outcomes
        )
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=actor_id,
            event_type=PackAuditEventType.CHAPTER_ADDED,
            metadata={
                "chapter_id": str(chapter.id),
                "title": chapter.title,
                "topic_count": len(data.topics),
            },
        )
        return chapter

    async def add_topic(
        self,
        school_id: uuid.UUID,
        chapter_id: uuid.UUID,
        data: TopicIn,
        *,
        actor_id: uuid.UUID,
    ) -> CurriculumTopic:
        chapter = (
            await self.db.execute(
                select(CurriculumChapter).where(
                    CurriculumChapter.id == chapter_id,
                    CurriculumChapter.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not chapter:
            raise PackError("Chapter not found")
        pack = await self.get_pack(school_id, chapter.pack_id)
        await self._require_draft(pack)
        topic = CurriculumTopic(
            school_id=school_id,
            chapter_id=chapter_id,
            title=data.title,
            order_index=data.order_index,
            concepts=data.concepts,
        )
        self.db.add(topic)
        await self.db.flush()
        await self._add_outcomes_to_topic(
            school_id=school_id, topic_id=topic.id, outcomes=data.learning_outcomes
        )
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=actor_id,
            event_type=PackAuditEventType.TOPIC_ADDED,
            metadata={
                "topic_id": str(topic.id),
                "chapter_id": str(chapter_id),
                "title": topic.title,
            },
        )
        return topic

    async def add_learning_outcome_to_topic(
        self,
        school_id: uuid.UUID,
        topic_id: uuid.UUID,
        data: LearningOutcomeIn,
        *,
        actor_id: uuid.UUID,
    ) -> CurriculumLearningOutcome:
        topic = (
            await self.db.execute(
                select(CurriculumTopic).where(
                    CurriculumTopic.id == topic_id,
                    CurriculumTopic.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not topic:
            raise PackError("Topic not found")
        chapter = (
            await self.db.execute(
                select(CurriculumChapter).where(
                    CurriculumChapter.id == topic.chapter_id,
                    CurriculumChapter.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not chapter:
            raise PackError("Chapter not found")
        pack = await self.get_pack(school_id, chapter.pack_id)
        await self._require_draft(pack)
        outcome = CurriculumLearningOutcome(
            school_id=school_id,
            topic_id=topic_id,
            code=data.code,
            description=data.description,
            order_index=data.order_index,
        )
        self.db.add(outcome)
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=actor_id,
            event_type=PackAuditEventType.LEARNING_OUTCOME_ADDED,
            metadata={
                "outcome_id": str(outcome.id),
                "topic_id": str(topic_id),
                "code": outcome.code,
            },
        )
        return outcome

    async def add_learning_outcome_to_chapter(
        self,
        school_id: uuid.UUID,
        chapter_id: uuid.UUID,
        data: LearningOutcomeIn,
        *,
        actor_id: uuid.UUID,
    ) -> CurriculumLearningOutcome:
        chapter = (
            await self.db.execute(
                select(CurriculumChapter).where(
                    CurriculumChapter.id == chapter_id,
                    CurriculumChapter.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not chapter:
            raise PackError("Chapter not found")
        pack = await self.get_pack(school_id, chapter.pack_id)
        await self._require_draft(pack)
        outcome = CurriculumLearningOutcome(
            school_id=school_id,
            chapter_id=chapter_id,
            code=data.code,
            description=data.description,
            order_index=data.order_index,
        )
        self.db.add(outcome)
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=actor_id,
            event_type=PackAuditEventType.LEARNING_OUTCOME_ADDED,
            metadata={
                "outcome_id": str(outcome.id),
                "chapter_id": str(chapter_id),
                "code": outcome.code,
            },
        )
        return outcome

    async def update_learning_outcome(
        self,
        school_id: uuid.UUID,
        outcome_id: uuid.UUID,
        data: LearningOutcomeUpdate,
        *,
        actor_id: uuid.UUID,
    ) -> CurriculumLearningOutcome:
        outcome = (
            await self.db.execute(
                select(CurriculumLearningOutcome).where(
                    CurriculumLearningOutcome.id == outcome_id,
                    CurriculumLearningOutcome.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if not outcome:
            raise PackError("Learning outcome not found")
        pack_id = await self._pack_id_for_outcome(outcome)
        pack = await self.get_pack(school_id, pack_id)
        await self._require_draft(pack)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(outcome, field, value)
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack_id,
            actor_id=actor_id,
            event_type=PackAuditEventType.LEARNING_OUTCOME_UPDATED,
            metadata={
                "outcome_id": str(outcome.id),
                "fields": list(data.model_dump(exclude_unset=True).keys()),
            },
        )
        return outcome

    async def _pack_id_for_outcome(self, outcome: CurriculumLearningOutcome) -> uuid.UUID:
        if outcome.topic_id:
            chapter_id = await self.db.scalar(
                select(CurriculumTopic.chapter_id).where(CurriculumTopic.id == outcome.topic_id)
            )
            if not chapter_id:
                raise PackError("Topic not found")
            pack_id = await self.db.scalar(
                select(CurriculumChapter.pack_id).where(CurriculumChapter.id == chapter_id)
            )
        else:
            pack_id = await self.db.scalar(
                select(CurriculumChapter.pack_id).where(
                    CurriculumChapter.id == outcome.chapter_id
                )
            )
        if not pack_id:
            raise PackError("Chapter not found")
        return pack_id

    async def _build_kg_spine_with_audit(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """Build Knowledge Graph spine; failures are recorded but do not block approval."""
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack_id,
            actor_id=actor_id,
            event_type=PackAuditEventType.KG_SPINE_STARTED,
        )
        try:
            from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService

            stats = await KnowledgeGraphService(self.db).build_spine_from_pack(
                school_id=school_id, pack_id=pack_id
            )
            await record_pack_audit_event(
                self.db,
                school_id=school_id,
                pack_id=pack_id,
                actor_id=actor_id,
                event_type=PackAuditEventType.KG_SPINE_SUCCEEDED,
                metadata={
                    "concept_count": stats.concepts_created,
                    "edge_count": stats.edges_created,
                },
            )
        except Exception as exc:
            error = str(exc)[:500]
            logger.exception(
                "curriculum_pack_kg_spine_failed",
                pack_id=str(pack_id),
                school_id=str(school_id),
            )
            await record_pack_audit_event(
                self.db,
                school_id=school_id,
                pack_id=pack_id,
                actor_id=actor_id,
                event_type=PackAuditEventType.KG_SPINE_FAILED,
                metadata={"error": error},
            )

    async def _eager_rag_index_with_audit(
        self, pack: CurriculumPack, *, actor_id: uuid.UUID
    ) -> None:
        """Eager RAG indexing on approve; idempotent when already successfully indexed."""
        if pack.rag_indexed_at is not None and not pack.rag_index_error:
            return

        from app.modules.ai.rag.service import RagService

        await record_pack_audit_event(
            self.db,
            school_id=pack.school_id,
            pack_id=pack.id,
            actor_id=actor_id,
            event_type=PackAuditEventType.RAG_INDEX_STARTED,
        )
        rag = self._rag or RagService(self.db)
        try:
            count = await rag.index_pack(pack)
            pack.rag_indexed_at = datetime.now(timezone.utc)
            pack.rag_index_topic_count = count
            pack.rag_index_error = None
            logger.info(
                "curriculum_pack_rag_indexed",
                pack_id=str(pack.id),
                school_id=str(pack.school_id),
                topic_count=count,
            )
            await record_pack_audit_event(
                self.db,
                school_id=pack.school_id,
                pack_id=pack.id,
                actor_id=actor_id,
                event_type=PackAuditEventType.RAG_INDEX_SUCCEEDED,
                metadata={
                    "vector_count": count,
                    "indexed_at": pack.rag_indexed_at.isoformat(),
                },
            )
        except Exception as exc:
            pack.rag_index_error = str(exc)[:500]
            logger.exception(
                "curriculum_pack_rag_index_failed",
                pack_id=str(pack.id),
                school_id=str(pack.school_id),
            )
            await record_pack_audit_event(
                self.db,
                school_id=pack.school_id,
                pack_id=pack.id,
                actor_id=actor_id,
                event_type=PackAuditEventType.RAG_INDEX_FAILED,
                metadata={"error": pack.rag_index_error},
            )
        await self.db.flush()

    async def retry_rag_index(
        self, school_id: uuid.UUID, pack_id: uuid.UUID, actor_id: uuid.UUID
    ) -> CurriculumPack:
        """Retry eager indexing for an approved pack (e.g. after a prior failure)."""
        pack = await self.get_pack(school_id, pack_id)
        if pack.status != PackStatus.APPROVED:
            raise PackError("Only approved packs can be indexed")
        if pack.rag_indexed_at is not None and not pack.rag_index_error:
            return pack
        await self._eager_rag_index_with_audit(pack, actor_id=actor_id)
        return pack

    async def approve_pack(
        self, school_id: uuid.UUID, pack_id: uuid.UUID, approved_by: uuid.UUID
    ) -> CurriculumPack:
        pack = await self.get_pack(school_id, pack_id)
        if pack.status == PackStatus.APPROVED:
            raise PackError("Pack is already approved")
        has_chapter = await self.db.scalar(
            select(func.count()).select_from(CurriculumChapter).where(CurriculumChapter.pack_id == pack_id)
        )
        if not has_chapter:
            raise PackError("Add at least one chapter before approving")
        pack.status = PackStatus.APPROVED
        pack.approved_by = approved_by
        pack.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=approved_by,
            event_type=PackAuditEventType.PACK_APPROVED,
            metadata={
                "version": pack.version,
                "approved_at": pack.approved_at.isoformat(),
            },
        )
        await self._build_kg_spine_with_audit(
            school_id=school_id, pack_id=pack_id, actor_id=approved_by
        )
        await self._eager_rag_index_with_audit(pack, actor_id=approved_by)
        return pack

    async def list_pack_audit(
        self, school_id: uuid.UUID, pack_id: uuid.UUID
    ) -> list[dict]:
        await self.get_pack(school_id, pack_id)
        from app.modules.curriculum.services.pack_audit import list_pack_audit_events

        return await list_pack_audit_events(self.db, school_id=school_id, pack_id=pack_id)
