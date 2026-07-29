"""Read-only passive mastery spine resolver.

Phase A resolves legacy topic signals into internal MasterySpineReference
objects only. It does not write mastery rows, switch sources, or alter product
behavior.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.modules.eui.schemas.educational_identity import EducationalIdentityReference
from app.modules.eui.services.educational_identity_resolver import (
    EducationalIdentityAmbiguous,
    EducationalIdentityNotFound,
    EducationalIdentityResolver,
)
from app.modules.mastery.schemas.mastery_spine import (
    MasterySpineAmbiguity,
    MasterySpineProvenance,
    MasterySpineReference,
    MasterySpineResolutionReference,
)
from app.modules.mastery.services.topic_norm import display_topic, normalize_topic


@dataclass(frozen=True)
class _Candidate:
    kind: str
    label: str
    topic_id: uuid.UUID | None = None
    concept_id: uuid.UUID | None = None
    learning_outcome_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None
    pack_id: uuid.UUID | None = None

    def evidence(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "pack_id": str(self.pack_id) if self.pack_id else None,
            "chapter_id": str(self.chapter_id) if self.chapter_id else None,
            "topic_id": str(self.topic_id) if self.topic_id else None,
            "concept_id": str(self.concept_id) if self.concept_id else None,
            "learning_outcome_id": (
                str(self.learning_outcome_id) if self.learning_outcome_id else None
            ),
        }


class MasterySpineResolver:
    """Resolve current topic evidence into an internal canonical spine reference."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.identity_resolver = EducationalIdentityResolver(db)

    async def resolve(
        self,
        reference: MasterySpineResolutionReference,
    ) -> MasterySpineReference:
        """Resolve using deterministic precedence without mutating state."""

        explicit = await self._resolve_explicit_curriculum_id(reference)
        if explicit is not None:
            return explicit

        identity_metadata = self._from_educational_identity_metadata(reference)
        if identity_metadata is not None:
            return identity_metadata

        pack = await self._approved_pack(reference)
        if pack is not None and _clean_label(reference.raw_label):
            label_result = await self._resolve_label_in_pack(reference, pack)
            if label_result is not None:
                return label_result

        if _clean_label(reference.raw_label):
            return self._legacy_fallback(reference)

        return self._unresolved(reference, reason="no_resolvable_spine_signal")

    async def _resolve_explicit_curriculum_id(
        self,
        reference: MasterySpineResolutionReference,
    ) -> MasterySpineReference | None:
        if reference.learning_outcome_id is not None:
            return await self._resolve_identity_reference(
                reference,
                EducationalIdentityReference(
                    school_id=reference.school_id,
                    learning_outcome_id=reference.learning_outcome_id,
                ),
                precedence=1,
                resolved_from="explicit_learning_outcome_id",
            )
        if reference.concept_id is not None:
            return await self._resolve_identity_reference(
                reference,
                EducationalIdentityReference(
                    school_id=reference.school_id,
                    concept_id=reference.concept_id,
                ),
                precedence=1,
                resolved_from="explicit_concept_id",
            )
        if reference.topic_id is not None:
            return await self._resolve_identity_reference(
                reference,
                EducationalIdentityReference(
                    school_id=reference.school_id,
                    topic_id=reference.topic_id,
                ),
                precedence=1,
                resolved_from="explicit_topic_id",
            )
        return None

    async def _resolve_identity_reference(
        self,
        reference: MasterySpineResolutionReference,
        identity_reference: EducationalIdentityReference,
        *,
        precedence: int,
        resolved_from: str,
    ) -> MasterySpineReference:
        try:
            identity = await self.identity_resolver.resolve(identity_reference)
        except EducationalIdentityAmbiguous as exc:
            return self._ambiguous(
                reference,
                reason="educational_identity_ambiguous",
                precedence=precedence,
                resolved_from=resolved_from,
                metadata={"error": str(exc)},
            )
        except EducationalIdentityNotFound as exc:
            return self._unresolved(
                reference,
                reason="educational_identity_not_found",
                precedence=precedence,
                resolved_from=resolved_from,
                metadata={"error": str(exc)},
            )

        return self._from_identity_metadata(
            reference,
            identity_id=identity.id,
            metadata=identity.metadata,
            label=(
                identity.topic
                or _first(identity.concepts)
                or _first(identity.learning_objectives)
            ),
            precedence=precedence,
            resolved_from=resolved_from,
            provenance_source=identity.provenance.source,
            provenance_source_id=identity.provenance.source_id,
        )

    def _from_educational_identity_metadata(
        self,
        reference: MasterySpineResolutionReference,
    ) -> MasterySpineReference | None:
        if not reference.educational_identity_id:
            return None
        metadata = reference.educational_identity_metadata
        if not metadata:
            return self._from_identity_metadata(
                reference,
                identity_id=reference.educational_identity_id,
                metadata={},
                label=_clean_label(reference.raw_label),
                precedence=2,
                resolved_from="educational_identity_id",
                provenance_source=reference.source,
                provenance_source_id=reference.educational_identity_id,
            )
        return self._from_identity_metadata(
            reference,
            identity_id=reference.educational_identity_id,
            metadata=metadata,
            label=_clean_label(reference.raw_label),
            precedence=2,
            resolved_from="educational_identity_metadata",
            provenance_source=reference.source,
            provenance_source_id=reference.educational_identity_id,
        )

    async def _approved_pack(
        self,
        reference: MasterySpineResolutionReference,
    ) -> CurriculumPack | None:
        filters = [
            CurriculumPack.school_id == reference.school_id,
            CurriculumPack.status == PackStatus.APPROVED,
        ]
        if reference.pack_id is not None:
            filters.append(CurriculumPack.id == reference.pack_id)
        else:
            if not (
                reference.class_id
                and reference.subject_id
                and reference.academic_year_id
            ):
                return None
            filters.extend([
                CurriculumPack.class_id == reference.class_id,
                CurriculumPack.subject_id == reference.subject_id,
                CurriculumPack.academic_year_id == reference.academic_year_id,
            ])
        return (
            await self.db.execute(
                select(CurriculumPack)
                .where(*filters)
                .order_by(CurriculumPack.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def _resolve_label_in_pack(
        self,
        reference: MasterySpineResolutionReference,
        pack: CurriculumPack,
    ) -> MasterySpineReference | None:
        label = _clean_label(reference.raw_label)
        if not label:
            return None

        exact = await self._label_candidates(pack=pack, label=label, exact=True)
        if len(exact) == 1:
            return await self._resolve_candidate(reference, exact[0], precedence=4)
        if len(exact) > 1:
            return self._ambiguous(
                reference,
                reason="multiple_exact_label_matches",
                candidates=exact,
                precedence=4,
                resolved_from="approved_pack_exact_label",
            )

        normalized = await self._label_candidates(pack=pack, label=label, exact=False)
        if len(normalized) == 1:
            return await self._resolve_candidate(reference, normalized[0], precedence=5)
        if len(normalized) > 1:
            return self._ambiguous(
                reference,
                reason="multiple_normalized_label_matches",
                candidates=normalized,
                precedence=5,
                resolved_from="approved_pack_normalized_label",
            )
        return None

    async def _resolve_candidate(
        self,
        reference: MasterySpineResolutionReference,
        candidate: _Candidate,
        *,
        precedence: int,
    ) -> MasterySpineReference:
        if candidate.learning_outcome_id is not None:
            identity_reference = EducationalIdentityReference(
                school_id=reference.school_id,
                learning_outcome_id=candidate.learning_outcome_id,
            )
        elif candidate.concept_id is not None:
            identity_reference = EducationalIdentityReference(
                school_id=reference.school_id,
                concept_id=candidate.concept_id,
            )
        elif candidate.topic_id is not None:
            identity_reference = EducationalIdentityReference(
                school_id=reference.school_id,
                topic_id=candidate.topic_id,
            )
        else:
            return self._legacy_fallback(reference)
        return await self._resolve_identity_reference(
            reference,
            identity_reference,
            precedence=precedence,
            resolved_from=f"approved_pack_{candidate.kind}_label",
        )

    async def _label_candidates(
        self,
        *,
        pack: CurriculumPack,
        label: str,
        exact: bool,
    ) -> list[_Candidate]:
        candidates: list[_Candidate] = []
        topic_rows = (
            await self.db.execute(
                select(CurriculumTopic, CurriculumChapter)
                .join(CurriculumChapter, CurriculumChapter.id == CurriculumTopic.chapter_id)
                .where(
                    CurriculumChapter.school_id == pack.school_id,
                    CurriculumChapter.pack_id == pack.id,
                    CurriculumTopic.school_id == pack.school_id,
                )
                .order_by(CurriculumChapter.order_index, CurriculumTopic.order_index)
            )
        ).all()
        for topic, chapter in topic_rows:
            if _matches(topic.title, label, exact=exact):
                candidates.append(
                    _Candidate(
                        kind="topic",
                        label=topic.title,
                        pack_id=pack.id,
                        chapter_id=chapter.id,
                        topic_id=topic.id,
                    )
                )

        concept_rows = (
            await self.db.execute(
                select(CurriculumConcept, CurriculumTopic, CurriculumChapter)
                .join(CurriculumTopic, CurriculumTopic.id == CurriculumConcept.topic_id)
                .join(CurriculumChapter, CurriculumChapter.id == CurriculumTopic.chapter_id)
                .where(
                    CurriculumConcept.school_id == pack.school_id,
                    CurriculumConcept.pack_id == pack.id,
                    CurriculumTopic.school_id == pack.school_id,
                    CurriculumChapter.school_id == pack.school_id,
                )
                .order_by(
                    CurriculumChapter.order_index,
                    CurriculumTopic.order_index,
                    CurriculumConcept.order_index,
                )
            )
        ).all()
        for concept, topic, chapter in concept_rows:
            if _matches(concept.title, label, exact=exact) or _matches(
                concept.slug, label, exact=exact
            ):
                candidates.append(
                    _Candidate(
                        kind="concept",
                        label=concept.title,
                        pack_id=pack.id,
                        chapter_id=chapter.id,
                        topic_id=topic.id,
                        concept_id=concept.id,
                    )
                )

        outcome_rows = (
            await self.db.execute(
                select(CurriculumLearningOutcome)
                .where(CurriculumLearningOutcome.school_id == pack.school_id)
                .order_by(CurriculumLearningOutcome.order_index)
            )
        ).scalars().all()
        topic_ids = {topic.id: (topic, chapter) for topic, chapter in topic_rows}
        chapter_ids = {chapter.id: chapter for _, chapter in topic_rows}
        for outcome in outcome_rows:
            if outcome.topic_id is not None and outcome.topic_id not in topic_ids:
                continue
            if outcome.chapter_id is not None and outcome.chapter_id not in chapter_ids:
                continue
            if _matches(outcome.code, label, exact=exact) or _matches(
                outcome.description, label, exact=exact
            ):
                topic: CurriculumTopic | None = None
                chapter: CurriculumChapter | None = None
                if outcome.topic_id is not None:
                    topic, chapter = topic_ids[outcome.topic_id]
                elif outcome.chapter_id is not None:
                    chapter = chapter_ids[outcome.chapter_id]
                candidates.append(
                    _Candidate(
                        kind="learning_outcome",
                        label=outcome.code or outcome.description,
                        pack_id=pack.id,
                        chapter_id=chapter.id if chapter else None,
                        topic_id=topic.id if topic else None,
                        learning_outcome_id=outcome.id,
                    )
                )
        return candidates

    def _from_identity_metadata(
        self,
        reference: MasterySpineResolutionReference,
        *,
        identity_id: str,
        metadata: dict[str, Any],
        label: str | None,
        precedence: int,
        resolved_from: str,
        provenance_source: str,
        provenance_source_id: str | None,
    ) -> MasterySpineReference:
        topic_id = _uuid_from(metadata.get("topic_id")) or reference.topic_id
        concept_id = _uuid_from(metadata.get("concept_id")) or reference.concept_id
        learning_outcome_id = (
            _uuid_from(metadata.get("learning_outcome_id")) or reference.learning_outcome_id
        )
        spine_level = _spine_level(
            topic_id=topic_id,
            concept_id=concept_id,
            learning_outcome_id=learning_outcome_id,
        )
        return MasterySpineReference(
            tenant_id=reference.effective_tenant_id,
            school_id=reference.school_id,
            academic_year_id=reference.academic_year_id,
            class_id=reference.class_id,
            subject_id=reference.subject_id,
            pack_id=_uuid_from(metadata.get("pack_id")) or reference.pack_id,
            chapter_id=_uuid_from(metadata.get("chapter_id")) or reference.chapter_id,
            topic_id=topic_id,
            concept_id=concept_id,
            learning_outcome_id=learning_outcome_id,
            educational_identity_id=identity_id,
            spine_level=spine_level,
            label=label or _clean_label(reference.raw_label),
            language=reference.language,
            resolution_status="resolved",
            authority_posture="canonical",
            provenance=MasterySpineProvenance(
                source=provenance_source,
                source_id=provenance_source_id,
                resolved_from=resolved_from,
                precedence=precedence,
                metadata={"phase": "passive_mastery_spine_resolution"},
            ),
            metadata={"source_switching": False, "passive": True},
        )

    def _legacy_fallback(
        self,
        reference: MasterySpineResolutionReference,
    ) -> MasterySpineReference:
        return MasterySpineReference(
            tenant_id=reference.effective_tenant_id,
            school_id=reference.school_id,
            academic_year_id=reference.academic_year_id,
            class_id=reference.class_id,
            subject_id=reference.subject_id,
            pack_id=reference.pack_id,
            chapter_id=reference.chapter_id,
            topic_id=reference.topic_id,
            concept_id=reference.concept_id,
            learning_outcome_id=reference.learning_outcome_id,
            educational_identity_id=reference.educational_identity_id,
            spine_level="label",
            label=display_topic(reference.raw_label or ""),
            language=reference.language,
            resolution_status="legacy_fallback",
            authority_posture="legacy",
            provenance=MasterySpineProvenance(
                source=reference.source,
                resolved_from="legacy_free_text_topic",
                precedence=6,
                metadata={"passive": True},
            ),
            metadata={"source_switching": False, "passive": True},
        )

    def _ambiguous(
        self,
        reference: MasterySpineResolutionReference,
        *,
        reason: str,
        candidates: list[_Candidate] | None = None,
        precedence: int,
        resolved_from: str,
        metadata: dict[str, Any] | None = None,
    ) -> MasterySpineReference:
        ambiguity = MasterySpineAmbiguity(
            reason=reason,
            candidates=tuple(candidate.evidence() for candidate in candidates or []),
            metadata=metadata or {},
        )
        return MasterySpineReference(
            tenant_id=reference.effective_tenant_id,
            school_id=reference.school_id,
            academic_year_id=reference.academic_year_id,
            class_id=reference.class_id,
            subject_id=reference.subject_id,
            pack_id=reference.pack_id,
            chapter_id=reference.chapter_id,
            topic_id=reference.topic_id,
            concept_id=reference.concept_id,
            learning_outcome_id=reference.learning_outcome_id,
            educational_identity_id=reference.educational_identity_id,
            spine_level="label" if _clean_label(reference.raw_label) else "unresolved",
            label=_clean_label(reference.raw_label),
            language=reference.language,
            resolution_status="ambiguous",
            authority_posture="ambiguous",
            provenance=MasterySpineProvenance(
                source=reference.source,
                resolved_from=resolved_from,
                precedence=precedence,
                metadata={"passive": True},
            ),
            ambiguities=(ambiguity,),
            metadata={"source_switching": False, "passive": True},
        )

    def _unresolved(
        self,
        reference: MasterySpineResolutionReference,
        *,
        reason: str,
        precedence: int = 7,
        resolved_from: str = "unresolved",
        metadata: dict[str, Any] | None = None,
    ) -> MasterySpineReference:
        ambiguity = MasterySpineAmbiguity(reason=reason, metadata=metadata or {})
        return MasterySpineReference(
            tenant_id=reference.effective_tenant_id,
            school_id=reference.school_id,
            academic_year_id=reference.academic_year_id,
            class_id=reference.class_id,
            subject_id=reference.subject_id,
            pack_id=reference.pack_id,
            chapter_id=reference.chapter_id,
            topic_id=reference.topic_id,
            concept_id=reference.concept_id,
            learning_outcome_id=reference.learning_outcome_id,
            educational_identity_id=reference.educational_identity_id,
            spine_level="unresolved",
            label=_clean_label(reference.raw_label),
            language=reference.language,
            resolution_status="unresolved",
            authority_posture="unresolved",
            provenance=MasterySpineProvenance(
                source=reference.source,
                resolved_from=resolved_from,
                precedence=precedence,
                metadata={"passive": True},
            ),
            ambiguities=(ambiguity,),
            metadata={"source_switching": False, "passive": True},
        )


def _matches(value: str | None, label: str, *, exact: bool) -> bool:
    if not value:
        return False
    return value.strip() == label if exact else normalize_topic(value) == normalize_topic(label)


def _clean_label(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = display_topic(value)
    return cleaned or None


def _uuid_from(value: Any) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    if value is None or value == "":
        return None
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _spine_level(
    *,
    topic_id: uuid.UUID | None,
    concept_id: uuid.UUID | None,
    learning_outcome_id: uuid.UUID | None,
) -> str:
    if learning_outcome_id is not None:
        return "learning_outcome"
    if concept_id is not None:
        return "concept"
    if topic_id is not None:
        return "topic"
    return "label"


def _first(values: tuple[str, ...] | list[str] | None) -> str | None:
    return values[0] if values else None
