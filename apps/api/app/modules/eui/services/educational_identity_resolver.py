"""Deterministic Educational Identity resolver.

Phase 1 Sprint 1 is intentionally read-only and passive:

* it reads existing CurriculumPack / Knowledge Graph data;
* it returns canonical EducationalIdentity objects;
* it does not persist IDs;
* it does not modify curriculum workflows;
* it does not migrate any consumer to depend on EducationalIdentity.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumTopic,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
    EducationalIdentityReference,
)
from app.modules.eui.services.educational_identity_cache import (
    EducationalIdentityCache,
    educational_identity_cache,
)
from app.modules.eui.services.educational_identity_id import (
    identity_alias,
    stable_identity_id,
)
from app.modules.eui.services.educational_identity_registry import (
    EducationalIdentityRegistry,
)

logger = logging.getLogger(__name__)


class EducationalIdentityResolutionError(RuntimeError):
    """Base class for Educational Identity resolution failures."""


class EducationalIdentityNotFound(EducationalIdentityResolutionError):
    """No supported educational identity could be resolved."""


class EducationalIdentityAmbiguous(EducationalIdentityResolutionError):
    """More than one canonical identity matched a reference."""


@dataclass(frozen=True)
class _PackContext:
    pack: CurriculumPack
    class_: Class
    subject: Subject
    curriculum: str
    curriculum_version: str


class EducationalIdentityResolver:
    """Read-only resolver for canonical EducationalIdentity objects."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        cache: EducationalIdentityCache = educational_identity_cache,
    ) -> None:
        self.db = db
        self.cache = cache

    async def resolve(self, reference: EducationalIdentityReference) -> EducationalIdentity:
        """Resolve a supported reference into one canonical EducationalIdentity."""

        match reference.resolution_kind:
            case "pack":
                return await self._resolve_pack(reference)
            case "chapter":
                return await self._resolve_chapter(reference)
            case "topic":
                return await self._resolve_topic(reference)
            case "concept":
                return await self._resolve_concept(reference)
            case "learning_outcome":
                return await self._resolve_learning_outcome(reference)
            case "label":
                return await self._resolve_label(reference)
            case _:
                raise EducationalIdentityNotFound("Educational identity reference is empty")

    async def build_registry_for_pack(
        self,
        *,
        school_id: uuid.UUID,
        pack_id: uuid.UUID,
    ) -> EducationalIdentityRegistry:
        """Build an in-memory read-only identity registry for a CurriculumPack."""

        reference = EducationalIdentityReference(school_id=school_id, pack_id=pack_id)
        pack = await self._pack(school_id=school_id, pack_id=pack_id)
        context = await self._pack_context(pack)
        identities: list[EducationalIdentity] = [await self._identity_for_pack(context, reference)]
        aliases: dict[str, str] = {
            f"pack:{pack.id}": identities[0].id,
            identity_alias("pack", pack.id): identities[0].id,
        }

        chapters = (
            await self.db.execute(
                select(CurriculumChapter)
                .where(
                    CurriculumChapter.school_id == school_id,
                    CurriculumChapter.pack_id == pack_id,
                )
                .order_by(CurriculumChapter.order_index, CurriculumChapter.title)
            )
        ).scalars().all()
        for chapter in chapters:
            chapter_ref = EducationalIdentityReference(school_id=school_id, chapter_id=chapter.id)
            chapter_identity = await self._identity_for_chapter(context, chapter, chapter_ref)
            identities.append(chapter_identity)
            _add_aliases(
                aliases,
                chapter_identity.id,
                f"chapter:{chapter.id}",
                identity_alias("chapter", chapter.id),
                identity_alias("chapter", chapter.number, chapter.title),
            )

            topics = (
                await self.db.execute(
                    select(CurriculumTopic)
                    .where(
                        CurriculumTopic.school_id == school_id,
                        CurriculumTopic.chapter_id == chapter.id,
                    )
                    .order_by(CurriculumTopic.order_index, CurriculumTopic.title)
                )
            ).scalars().all()
            for topic in topics:
                topic_ref = EducationalIdentityReference(school_id=school_id, topic_id=topic.id)
                topic_identity = await self._identity_for_topic(context, chapter, topic, topic_ref)
                identities.append(topic_identity)
                _add_aliases(
                    aliases,
                    topic_identity.id,
                    f"topic:{topic.id}",
                    identity_alias("topic", topic.id),
                    identity_alias("topic", chapter.title, topic.title),
                )

                concepts = await self._concept_rows(topic_id=topic.id, school_id=school_id)
                for concept in concepts:
                    concept_ref = EducationalIdentityReference(
                        school_id=school_id,
                        concept_id=concept.id,
                    )
                    concept_identity = await self._identity_for_concept(
                        context,
                        chapter,
                        topic,
                        concept,
                        concept_ref,
                    )
                    identities.append(concept_identity)
                    _add_aliases(
                        aliases,
                        concept_identity.id,
                        f"concept:{concept.id}",
                        identity_alias("concept", concept.id),
                        identity_alias("concept", topic.title, concept.slug),
                    )

                topic_outcomes = (
                    await self.db.execute(
                        select(CurriculumLearningOutcome)
                        .where(
                            CurriculumLearningOutcome.school_id == school_id,
                            CurriculumLearningOutcome.topic_id == topic.id,
                        )
                        .order_by(
                            CurriculumLearningOutcome.order_index,
                            CurriculumLearningOutcome.code,
                            CurriculumLearningOutcome.description,
                        )
                    )
                ).scalars().all()
                for outcome in topic_outcomes:
                    outcome_ref = EducationalIdentityReference(
                        school_id=school_id,
                        learning_outcome_id=outcome.id,
                    )
                    outcome_identity = await self._identity_for_learning_outcome(
                        context,
                        chapter,
                        topic,
                        outcome,
                        outcome_ref,
                    )
                    identities.append(outcome_identity)
                    _add_aliases(
                        aliases,
                        outcome_identity.id,
                        f"learning_outcome:{outcome.id}",
                        identity_alias("learning_outcome", outcome.id),
                        identity_alias(
                            "learning_outcome",
                            outcome.code or outcome.description,
                        ),
                    )

            outcomes = (
                await self.db.execute(
                    select(CurriculumLearningOutcome)
                    .where(
                        CurriculumLearningOutcome.school_id == school_id,
                        CurriculumLearningOutcome.chapter_id == chapter.id,
                    )
                    .order_by(
                        CurriculumLearningOutcome.order_index,
                        CurriculumLearningOutcome.code,
                        CurriculumLearningOutcome.description,
                    )
                )
            ).scalars().all()
            for outcome in outcomes:
                outcome_ref = EducationalIdentityReference(
                    school_id=school_id,
                    learning_outcome_id=outcome.id,
                )
                outcome_identity = await self._identity_for_learning_outcome(
                    context,
                    chapter,
                    None,
                    outcome,
                    outcome_ref,
                )
                identities.append(outcome_identity)
                _add_aliases(
                    aliases,
                    outcome_identity.id,
                    f"learning_outcome:{outcome.id}",
                    identity_alias("learning_outcome", outcome.id),
                    identity_alias("learning_outcome", outcome.code or outcome.description),
                )

        return EducationalIdentityRegistry.from_identities(identities, aliases=aliases)

    async def _resolve_pack(self, reference: EducationalIdentityReference) -> EducationalIdentity:
        assert reference.pack_id is not None
        cache_key = _cache_key("pack", reference.school_id, reference.pack_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        pack = await self._pack(school_id=reference.school_id, pack_id=reference.pack_id)
        identity = await self._identity_for_pack(await self._pack_context(pack), reference)
        self.cache.set(cache_key, identity)
        return identity

    async def _resolve_chapter(
        self,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        assert reference.chapter_id is not None
        cache_key = _cache_key("chapter", reference.school_id, reference.chapter_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        chapter = await self._chapter(reference.school_id, reference.chapter_id)
        pack = await self._pack(school_id=reference.school_id, pack_id=chapter.pack_id)
        identity = await self._identity_for_chapter(
            await self._pack_context(pack),
            chapter,
            reference,
        )
        self.cache.set(cache_key, identity)
        return identity

    async def _resolve_topic(self, reference: EducationalIdentityReference) -> EducationalIdentity:
        assert reference.topic_id is not None
        cache_key = _cache_key("topic", reference.school_id, reference.topic_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        topic = await self._topic(reference.school_id, reference.topic_id)
        chapter = await self._chapter(reference.school_id, topic.chapter_id)
        pack = await self._pack(school_id=reference.school_id, pack_id=chapter.pack_id)
        identity = await self._identity_for_topic(
            await self._pack_context(pack),
            chapter,
            topic,
            reference,
        )
        self.cache.set(cache_key, identity)
        return identity

    async def _resolve_concept(
        self,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        assert reference.concept_id is not None
        cache_key = _cache_key("concept", reference.school_id, reference.concept_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        concept = await self._concept(reference.school_id, reference.concept_id)
        topic = await self._topic(reference.school_id, concept.topic_id)
        chapter = await self._chapter(reference.school_id, topic.chapter_id)
        pack = await self._pack(school_id=reference.school_id, pack_id=chapter.pack_id)
        identity = await self._identity_for_concept(
            await self._pack_context(pack),
            chapter,
            topic,
            concept,
            reference,
        )
        self.cache.set(cache_key, identity)
        return identity

    async def _resolve_learning_outcome(
        self,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        assert reference.learning_outcome_id is not None
        cache_key = _cache_key(
            "learning_outcome",
            reference.school_id,
            reference.learning_outcome_id,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        outcome = await self._learning_outcome(reference.school_id, reference.learning_outcome_id)
        topic: CurriculumTopic | None = None
        if outcome.topic_id is not None:
            topic = await self._topic(reference.school_id, outcome.topic_id)
            chapter = await self._chapter(reference.school_id, topic.chapter_id)
        elif outcome.chapter_id is not None:
            chapter = await self._chapter(reference.school_id, outcome.chapter_id)
        else:
            raise EducationalIdentityNotFound(
                f"Learning outcome has no topic or chapter scope: {outcome.id}"
            )
        pack = await self._pack(school_id=reference.school_id, pack_id=chapter.pack_id)
        identity = await self._identity_for_learning_outcome(
            await self._pack_context(pack),
            chapter,
            topic,
            outcome,
            reference,
        )
        self.cache.set(cache_key, identity)
        return identity

    async def _resolve_label(self, reference: EducationalIdentityReference) -> EducationalIdentity:
        assert reference.raw_label is not None
        label = identity_alias("label", reference.raw_label)
        candidates: list[EducationalIdentity] = []

        pack_query = (
            select(CurriculumPack)
            .join(Class, Class.id == CurriculumPack.class_id)
            .join(Subject, Subject.id == CurriculumPack.subject_id)
            .where(CurriculumPack.school_id == reference.school_id)
        )
        if reference.board:
            pack_query = pack_query.where(
                func.lower(CurriculumPack.board) == reference.board.lower()
            )
        if reference.grade:
            pack_query = pack_query.where(func.lower(Class.grade) == reference.grade.lower())
        if reference.subject:
            pack_query = pack_query.where(func.lower(Subject.name) == reference.subject.lower())

        packs = (
            await self.db.execute(pack_query.order_by(CurriculumPack.created_at))
        ).scalars().all()
        for pack in packs:
            registry = await self.build_registry_for_pack(
                school_id=reference.school_id,
                pack_id=pack.id,
            )
            candidates.extend(
                identity
                for identity in registry.identities
                if _identity_label_alias(identity) == label
            )

        if not candidates:
            raise EducationalIdentityNotFound(
                f"Educational identity label not found: {reference.raw_label}"
            )

        ranked = sorted(
            candidates,
            key=lambda item: _ENTITY_SPECIFICITY.get(str(item.metadata.get("entity_type")), 0),
            reverse=True,
        )
        highest = _ENTITY_SPECIFICITY.get(str(ranked[0].metadata.get("entity_type")), 0)
        top = [
            item
            for item in ranked
            if _ENTITY_SPECIFICITY.get(str(item.metadata.get("entity_type")), 0) == highest
        ]
        unique_ids = {item.id for item in top}
        if len(unique_ids) > 1:
            raise EducationalIdentityAmbiguous(
                f"Educational identity label is ambiguous: {reference.raw_label}"
            )
        return top[0]

    async def _identity_for_pack(
        self,
        context: _PackContext,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        identity_id = stable_identity_id(
            board=context.pack.board,
            curriculum=context.curriculum,
            curriculum_version=context.curriculum_version,
            grade=context.class_.grade,
            subject=context.subject.name,
        )
        return self._identity(
            identity_id=identity_id,
            context=context,
            reference=reference,
            entity_type="pack",
            source_id=context.pack.id,
            metadata={
                "pack_id": str(context.pack.id),
                "class_id": str(context.class_.id),
                "subject_id": str(context.subject.id),
                "academic_year_id": str(context.pack.academic_year_id),
            },
        )

    async def _identity_for_chapter(
        self,
        context: _PackContext,
        chapter: CurriculumChapter,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        outcomes = await self._learning_outcome_labels(
            school_id=context.pack.school_id,
            chapter_id=chapter.id,
        )
        identity_id = stable_identity_id(
            board=context.pack.board,
            curriculum=context.curriculum,
            curriculum_version=context.curriculum_version,
            grade=context.class_.grade,
            subject=context.subject.name,
            chapter_number=chapter.number,
            chapter=chapter.title,
        )
        return self._identity(
            identity_id=identity_id,
            context=context,
            reference=reference,
            entity_type="chapter",
            source_id=chapter.id,
            chapter=chapter.title,
            learning_objectives=outcomes,
            metadata={
                "pack_id": str(context.pack.id),
                "chapter_id": str(chapter.id),
                "chapter_number": chapter.number,
            },
        )

    async def _identity_for_topic(
        self,
        context: _PackContext,
        chapter: CurriculumChapter,
        topic: CurriculumTopic,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        concepts = await self._concept_labels(
            school_id=context.pack.school_id,
            topic_id=topic.id,
            fallback=topic.concepts,
        )
        outcomes = await self._learning_outcome_labels(
            school_id=context.pack.school_id,
            topic_id=topic.id,
        )
        identity_id = stable_identity_id(
            board=context.pack.board,
            curriculum=context.curriculum,
            curriculum_version=context.curriculum_version,
            grade=context.class_.grade,
            subject=context.subject.name,
            chapter_number=chapter.number,
            chapter=chapter.title,
            topic=topic.title,
        )
        return self._identity(
            identity_id=identity_id,
            context=context,
            reference=reference,
            entity_type="topic",
            source_id=topic.id,
            chapter=chapter.title,
            topic=topic.title,
            concepts=concepts,
            learning_objectives=outcomes,
            metadata={
                "pack_id": str(context.pack.id),
                "chapter_id": str(chapter.id),
                "topic_id": str(topic.id),
            },
        )

    async def _identity_for_concept(
        self,
        context: _PackContext,
        chapter: CurriculumChapter,
        topic: CurriculumTopic,
        concept: CurriculumConcept,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        identity_id = stable_identity_id(
            board=context.pack.board,
            curriculum=context.curriculum,
            curriculum_version=context.curriculum_version,
            grade=context.class_.grade,
            subject=context.subject.name,
            chapter_number=chapter.number,
            chapter=chapter.title,
            topic=topic.title,
            concept=concept.slug,
        )
        return self._identity(
            identity_id=identity_id,
            context=context,
            reference=reference,
            entity_type="concept",
            source_id=concept.id,
            chapter=chapter.title,
            topic=topic.title,
            concepts=(concept.title,),
            metadata={
                "pack_id": str(context.pack.id),
                "chapter_id": str(chapter.id),
                "topic_id": str(topic.id),
                "concept_id": str(concept.id),
                "concept_slug": concept.slug,
            },
        )

    async def _identity_for_learning_outcome(
        self,
        context: _PackContext,
        chapter: CurriculumChapter,
        topic: CurriculumTopic | None,
        outcome: CurriculumLearningOutcome,
        reference: EducationalIdentityReference,
    ) -> EducationalIdentity:
        outcome_label = outcome.code or outcome.description
        identity_id = stable_identity_id(
            board=context.pack.board,
            curriculum=context.curriculum,
            curriculum_version=context.curriculum_version,
            grade=context.class_.grade,
            subject=context.subject.name,
            chapter_number=chapter.number,
            chapter=chapter.title,
            topic=topic.title if topic else None,
            learning_objective=outcome_label,
        )
        return self._identity(
            identity_id=identity_id,
            context=context,
            reference=reference,
            entity_type="learning_outcome",
            source_id=outcome.id,
            chapter=chapter.title,
            topic=topic.title if topic else None,
            learning_objectives=(outcome.description,),
            metadata={
                "pack_id": str(context.pack.id),
                "chapter_id": str(chapter.id),
                "topic_id": str(topic.id) if topic else None,
                "learning_outcome_id": str(outcome.id),
                "learning_outcome_code": outcome.code,
            },
        )

    def _identity(
        self,
        *,
        identity_id: str,
        context: _PackContext,
        reference: EducationalIdentityReference,
        entity_type: str,
        source_id: uuid.UUID,
        chapter: str | None = None,
        topic: str | None = None,
        concepts: Iterable[str] = (),
        competencies: Iterable[str] = (),
        learning_objectives: Iterable[str] = (),
        metadata: dict[str, object | None] | None = None,
    ) -> EducationalIdentity:
        return EducationalIdentity(
            id=identity_id,
            tenant_id=context.pack.school_id,
            board=context.pack.board,
            curriculum=context.curriculum,
            curriculum_version=context.curriculum_version,
            grade=context.class_.grade,
            subject=context.subject.name,
            chapter=chapter,
            topic=topic,
            concepts=_dedupe(concepts),
            competencies=_dedupe(competencies),
            learning_objectives=_dedupe(learning_objectives),
            metadata={
                "entity_type": entity_type,
                **{key: value for key, value in (metadata or {}).items() if value is not None},
            },
            provenance=EducationalIdentityProvenance(
                source="curriculum_pack",
                source_id=str(source_id),
                source_version=context.curriculum_version,
                resolved_from=reference.resolution_kind,
                metadata={
                    "authorization": "EUI-PH1-AUTH-001",
                    "passive": True,
                },
            ),
        )

    async def _pack_context(self, pack: CurriculumPack) -> _PackContext:
        class_ = (
            await self.db.execute(
                select(Class).where(Class.id == pack.class_id, Class.school_id == pack.school_id)
            )
        ).scalar_one_or_none()
        subject = (
            await self.db.execute(
                select(Subject).where(
                    Subject.id == pack.subject_id,
                    Subject.school_id == pack.school_id,
                )
            )
        ).scalar_one_or_none()
        if class_ is None or subject is None:
            raise EducationalIdentityNotFound(f"CurriculumPack scope is incomplete: {pack.id}")
        curriculum = _first_non_empty(pack.book_title, pack.publisher, pack.board)
        curriculum_version = _first_non_empty(pack.edition, f"v{pack.version}")
        return _PackContext(
            pack=pack,
            class_=class_,
            subject=subject,
            curriculum=curriculum,
            curriculum_version=curriculum_version,
        )

    async def _pack(self, *, school_id: uuid.UUID, pack_id: uuid.UUID) -> CurriculumPack:
        pack = (
            await self.db.execute(
                select(CurriculumPack).where(
                    CurriculumPack.school_id == school_id,
                    CurriculumPack.id == pack_id,
                )
            )
        ).scalar_one_or_none()
        if pack is None:
            raise EducationalIdentityNotFound(f"CurriculumPack not found: {pack_id}")
        return pack

    async def _chapter(self, school_id: uuid.UUID, chapter_id: uuid.UUID) -> CurriculumChapter:
        chapter = (
            await self.db.execute(
                select(CurriculumChapter).where(
                    CurriculumChapter.school_id == school_id,
                    CurriculumChapter.id == chapter_id,
                )
            )
        ).scalar_one_or_none()
        if chapter is None:
            raise EducationalIdentityNotFound(f"CurriculumChapter not found: {chapter_id}")
        return chapter

    async def _topic(self, school_id: uuid.UUID, topic_id: uuid.UUID) -> CurriculumTopic:
        topic = (
            await self.db.execute(
                select(CurriculumTopic).where(
                    CurriculumTopic.school_id == school_id,
                    CurriculumTopic.id == topic_id,
                )
            )
        ).scalar_one_or_none()
        if topic is None:
            raise EducationalIdentityNotFound(f"CurriculumTopic not found: {topic_id}")
        return topic

    async def _concept(self, school_id: uuid.UUID, concept_id: uuid.UUID) -> CurriculumConcept:
        concept = (
            await self.db.execute(
                select(CurriculumConcept).where(
                    CurriculumConcept.school_id == school_id,
                    CurriculumConcept.id == concept_id,
                )
            )
        ).scalar_one_or_none()
        if concept is None:
            raise EducationalIdentityNotFound(f"CurriculumConcept not found: {concept_id}")
        return concept

    async def _learning_outcome(
        self,
        school_id: uuid.UUID,
        outcome_id: uuid.UUID,
    ) -> CurriculumLearningOutcome:
        outcome = (
            await self.db.execute(
                select(CurriculumLearningOutcome).where(
                    CurriculumLearningOutcome.school_id == school_id,
                    CurriculumLearningOutcome.id == outcome_id,
                )
            )
        ).scalar_one_or_none()
        if outcome is None:
            raise EducationalIdentityNotFound(
                f"CurriculumLearningOutcome not found: {outcome_id}"
            )
        return outcome

    async def _concept_rows(
        self,
        *,
        school_id: uuid.UUID,
        topic_id: uuid.UUID,
    ) -> list[CurriculumConcept]:
        return list(
            (
                await self.db.execute(
                    select(CurriculumConcept)
                    .where(
                        CurriculumConcept.school_id == school_id,
                        CurriculumConcept.topic_id == topic_id,
                    )
                    .order_by(CurriculumConcept.order_index, CurriculumConcept.title)
                )
            ).scalars().all()
        )

    async def _concept_labels(
        self,
        *,
        school_id: uuid.UUID,
        topic_id: uuid.UUID,
        fallback: list | None,
    ) -> tuple[str, ...]:
        rows = await self._concept_rows(school_id=school_id, topic_id=topic_id)
        if rows:
            return _dedupe(row.title for row in rows)
        return _dedupe(str(item) for item in (fallback or []) if str(item).strip())

    async def _learning_outcome_labels(
        self,
        *,
        school_id: uuid.UUID,
        chapter_id: uuid.UUID | None = None,
        topic_id: uuid.UUID | None = None,
    ) -> tuple[str, ...]:
        query = select(CurriculumLearningOutcome).where(
            CurriculumLearningOutcome.school_id == school_id
        )
        if topic_id is not None:
            query = query.where(CurriculumLearningOutcome.topic_id == topic_id)
        elif chapter_id is not None:
            query = query.where(CurriculumLearningOutcome.chapter_id == chapter_id)
        else:
            return ()
        rows = (
            await self.db.execute(
                query.order_by(
                    CurriculumLearningOutcome.order_index,
                    CurriculumLearningOutcome.code,
                    CurriculumLearningOutcome.description,
                )
            )
        ).scalars().all()
        return _dedupe(row.description for row in rows)


_ENTITY_SPECIFICITY = {
    "pack": 1,
    "chapter": 2,
    "topic": 3,
    "concept": 4,
    "learning_outcome": 4,
}


def _identity_label_alias(identity: EducationalIdentity) -> str:
    entity_type = str(identity.metadata.get("entity_type"))
    if entity_type == "pack":
        return identity_alias("label", identity.subject)
    if entity_type == "chapter":
        return identity_alias("label", identity.chapter)
    if entity_type == "topic":
        return identity_alias("label", identity.topic)
    if entity_type == "concept" and identity.concepts:
        return identity_alias("label", identity.concepts[0])
    if entity_type == "learning_outcome" and identity.learning_objectives:
        return identity_alias("label", identity.learning_objectives[0])
    return identity_alias("label", identity.id)


def _add_aliases(aliases: dict[str, str], identity_id: str, *values: str) -> None:
    for value in values:
        if value:
            aliases.setdefault(value, identity_id)


def _cache_key(kind: str, school_id: uuid.UUID, value: uuid.UUID) -> str:
    return f"{kind}:{school_id}:{value}"


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return tuple(result)


def _first_non_empty(*values: object) -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return "unknown"
