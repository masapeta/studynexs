"""Pack readiness — retrievable topics and indexing prerequisites."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import CurriculumChapter, CurriculumTopic


@dataclass(frozen=True)
class PackReadinessSnapshot:
    chapter_count: int
    topic_count: int
    retrievable_topic_count: int

    @property
    def has_retrievable_topics(self) -> bool:
        return self.retrievable_topic_count > 0


async def snapshot_pack_readiness(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
) -> PackReadinessSnapshot:
    chapter_count = int(
        await db.scalar(
            select(func.count())
            .select_from(CurriculumChapter)
            .where(
                CurriculumChapter.pack_id == pack_id,
                CurriculumChapter.school_id == school_id,
            )
        )
        or 0
    )
    topic_count = int(
        await db.scalar(
            select(func.count())
            .select_from(CurriculumTopic)
            .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
            .where(
                CurriculumChapter.pack_id == pack_id,
                CurriculumChapter.school_id == school_id,
            )
        )
        or 0
    )
    retrievable_topic_count = int(
        await db.scalar(
            select(func.count())
            .select_from(CurriculumTopic)
            .join(CurriculumChapter, CurriculumTopic.chapter_id == CurriculumChapter.id)
            .where(
                CurriculumChapter.pack_id == pack_id,
                CurriculumChapter.school_id == school_id,
                CurriculumTopic.title.is_not(None),
                func.length(func.trim(CurriculumTopic.title)) > 0,
            )
        )
        or 0
    )
    return PackReadinessSnapshot(
        chapter_count=chapter_count,
        topic_count=topic_count,
        retrievable_topic_count=retrievable_topic_count,
    )


def approval_blockers(snapshot: PackReadinessSnapshot) -> list[str]:
    blockers: list[str] = []
    if snapshot.chapter_count == 0:
        blockers.append("Add at least one chapter before approving.")
    elif not snapshot.has_retrievable_topics:
        blockers.append(
            "Add at least one topic with curriculum content — chapters alone are not retrievable."
        )
    return blockers
