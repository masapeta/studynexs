"""Curriculum pack service — create/build draft, approve to immutable, version."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.modules.curriculum.schemas.pack import ChapterIn, PackCreate, PackUpdate, TopicIn


class PackError(ValueError):
    """Pack cannot be created or modified."""


class PackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_pack(
        self, school_id: uuid.UUID, data: PackCreate, created_by: uuid.UUID
    ) -> CurriculumPack:
        scope = TenantScope(self.db, school_id)
        await scope.subject_in_class(data.subject_id, data.class_id)
        await scope.academic_year(data.academic_year_id)

        # Next version for this scope (1 if none yet).
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

    async def update_pack(
        self, school_id: uuid.UUID, pack_id: uuid.UUID, data: PackUpdate
    ) -> CurriculumPack:
        pack = await self.get_pack(school_id, pack_id)
        await self._require_draft(pack)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pack, field, value)
        await self.db.flush()
        return pack

    async def add_chapter(
        self, school_id: uuid.UUID, pack_id: uuid.UUID, data: ChapterIn
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
            self.db.add(
                CurriculumTopic(
                    school_id=school_id,
                    chapter_id=chapter.id,
                    title=t.title,
                    order_index=t.order_index,
                    concepts=t.concepts,
                )
            )
        await self.db.flush()
        return chapter

    async def add_topic(
        self, school_id: uuid.UUID, chapter_id: uuid.UUID, data: TopicIn
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
        return topic

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
        from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService

        await KnowledgeGraphService(self.db).build_spine_from_pack(
            school_id=school_id, pack_id=pack_id
        )
        return pack
