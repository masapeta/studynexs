"""Build PackDetailOut from pack + related rows."""

from __future__ import annotations

from app.modules.curriculum.schemas.pack import (
    ChapterOut,
    LearningOutcomeOut,
    PackDetailOut,
    TopicOut,
)
from app.modules.curriculum.services.pack_service import PackService


async def build_pack_detail(svc: PackService, pack) -> PackDetailOut:
    chapters = await svc.get_chapters(pack.id)
    chapter_ids = [c.id for c in chapters]
    topics_by_ch = await svc.get_topics_for_chapters(chapter_ids)
    topic_ids = [t.id for topics in topics_by_ch.values() for t in topics]
    outcomes_by_topic = await svc.get_outcomes_for_topics(topic_ids)
    outcomes_by_chapter = await svc.get_outcomes_for_chapters(chapter_ids)
    out = PackDetailOut.model_validate(pack)
    out.chapters = [
        ChapterOut(
            id=c.id,
            number=c.number,
            title=c.title,
            order_index=c.order_index,
            learning_outcomes=[
                LearningOutcomeOut.model_validate(lo)
                for lo in outcomes_by_chapter.get(c.id, [])
            ],
            topics=[
                TopicOut(
                    id=t.id,
                    title=t.title,
                    order_index=t.order_index,
                    concepts=t.concepts,
                    learning_outcomes=[
                        LearningOutcomeOut.model_validate(lo)
                        for lo in outcomes_by_topic.get(t.id, [])
                    ],
                )
                for t in topics_by_ch.get(c.id, [])
            ],
        )
        for c in chapters
    ]
    return out
