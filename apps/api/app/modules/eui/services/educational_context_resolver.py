"""Deterministic passive Educational Context resolver.

Sprint 2 is intentionally read-only and passive:

* it resolves context from existing references and Educational Identity;
* it records precedence conflicts and ambiguity;
* it does not persist context;
* it does not migrate any consumer to depend on Educational Context.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextAmbiguity,
    EducationalContextConflict,
    EducationalContextProvenance,
    EducationalContextReference,
)
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityReference,
)
from app.modules.eui.services.educational_context_cache import (
    EducationalContextCache,
    educational_context_cache,
)
from app.modules.eui.services.educational_identity_resolver import EducationalIdentityResolver


class EducationalContextResolutionError(RuntimeError):
    """Base class for Educational Context resolution failures."""


class EducationalContextNotFound(EducationalContextResolutionError):
    """No supported educational context could be resolved."""


@dataclass
class _ContextBuilder:
    values: dict[str, Any]
    field_sources: dict[str, str]
    conflicts: list[EducationalContextConflict]
    ambiguities: list[EducationalContextAmbiguity]

    def apply(self, field: str, value: Any, source: str) -> None:
        if _empty(value):
            return
        if field not in self.values or _empty(self.values[field]):
            self.values[field] = value
            self.field_sources[field] = source
            return
        if not _equivalent(self.values[field], value):
            self.conflicts.append(
                EducationalContextConflict(
                    field=field,
                    chosen_source=self.field_sources[field],
                    rejected_source=source,
                    chosen_value=_display(self.values[field]),
                    rejected_value=_display(value),
                )
            )


class EducationalContextResolver:
    """Read-only resolver for canonical EducationalContext objects."""

    def __init__(
        self,
        db: AsyncSession | None = None,
        *,
        cache: EducationalContextCache = educational_context_cache,
        identity_resolver: EducationalIdentityResolver | None = None,
    ) -> None:
        self.db = db
        self.cache = cache
        self.identity_resolver = identity_resolver

    async def resolve(self, reference: EducationalContextReference) -> EducationalContext:
        """Resolve a supported reference into passive EducationalContext."""

        cache_key = _cache_key(reference)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        identity = await self._resolve_identity(reference)
        context = self._context_from_reference(reference, identity)
        self.cache.set(cache_key, context)
        return context

    async def _resolve_identity(
        self,
        reference: EducationalContextReference,
    ) -> EducationalIdentity | None:
        if reference.educational_identity is not None:
            return reference.educational_identity
        if not _has_identity_reference(reference):
            return None
        resolver = self.identity_resolver
        if resolver is None:
            if self.db is None:
                return None
            resolver = EducationalIdentityResolver(self.db)
        return await resolver.resolve(
            EducationalIdentityReference(
                school_id=reference.school_id,
                pack_id=reference.pack_id,
                chapter_id=reference.chapter_id,
                topic_id=reference.topic_id,
                concept_id=reference.concept_id,
                learning_outcome_id=reference.learning_outcome_id,
                raw_label=reference.metadata.get("raw_label"),
                board=reference.board,
                grade=reference.grade,
                subject=reference.subject,
                artifact_type=reference.artifact_type,
            )
        )

    def _context_from_reference(
        self,
        reference: EducationalContextReference,
        identity: EducationalIdentity | None,
    ) -> EducationalContext:
        builder = _ContextBuilder(
            values={"tenant_id": reference.school_id},
            field_sources={"tenant_id": "trusted_runtime_scope"},
            conflicts=[],
            ambiguities=[],
        )

        if len(reference.candidate_context_ids) > 1 and identity is None:
            builder.ambiguities.append(
                EducationalContextAmbiguity(
                    reason="multiple_context_candidates",
                    source_fields=("candidate_context_ids",),
                    candidates=reference.candidate_context_ids,
                )
            )

        self._apply_explicit_references(builder, reference)
        if identity is not None:
            self._apply_identity(builder, identity)
        self._apply_runtime_metadata(builder, reference)

        if identity is None and not _has_minimum_context(builder.values):
            if builder.ambiguities:
                return self._build_context(reference, builder, status="ambiguous")
            raise EducationalContextNotFound("Educational Context reference is incomplete")

        status = self._resolution_status(builder)
        return self._build_context(reference, builder, status=status)

    def _apply_identity(
        self,
        builder: _ContextBuilder,
        identity: EducationalIdentity,
    ) -> None:
        source = "educational_identity"
        builder.apply("educational_identity_id", identity.id, source)
        builder.apply("board", identity.board, source)
        builder.apply("curriculum", identity.curriculum, source)
        builder.apply("curriculum_version", identity.curriculum_version, source)
        builder.apply("grade", identity.grade, source)
        builder.apply("subject", identity.subject, source)
        builder.apply("chapter", identity.chapter, source)
        builder.apply("topic", identity.topic, source)
        builder.apply("concepts", identity.concepts, source)
        builder.apply("competencies", identity.competencies, source)
        builder.apply("learning_objectives", identity.learning_objectives, source)
        builder.apply("language_medium", identity.language, source)
        pack_id = _uuid_from_metadata(identity.metadata.get("pack_id"))
        if pack_id:
            builder.apply("curriculum_pack_id", pack_id, "curriculum_pack_metadata")

    def _apply_explicit_references(
        self,
        builder: _ContextBuilder,
        reference: EducationalContextReference,
    ) -> None:
        source = "explicit_artifact_reference"
        builder.apply("curriculum_pack_id", reference.pack_id, source)
        builder.apply("educational_identity_id", reference.educational_identity_id, source)
        builder.apply("academic_year_id", reference.academic_year_id, source)
        if reference.artifact_type:
            builder.apply("artifact_type", reference.artifact_type, source)
        if reference.artifact_id:
            builder.apply("artifact_id", reference.artifact_id, source)

    def _apply_runtime_metadata(
        self,
        builder: _ContextBuilder,
        reference: EducationalContextReference,
    ) -> None:
        source = "runtime_metadata"
        for field in (
            "academic_year",
            "board",
            "curriculum",
            "curriculum_version",
            "grade",
            "section",
            "subject",
            "chapter",
            "topic",
            "concepts",
            "competencies",
            "learning_objectives",
            "assessment_mode",
            "language_medium",
            "evidence_posture",
        ):
            builder.apply(field, getattr(reference, field), source)

    def _build_context(
        self,
        reference: EducationalContextReference,
        builder: _ContextBuilder,
        *,
        status: str,
    ) -> EducationalContext:
        values = dict(builder.values)
        metadata = {
            "authorization": "EUI-PH1-SP2-AUTH-001",
            "passive": True,
            "reference_kind": reference.resolution_kind,
        }
        if reference.artifact_type:
            metadata["artifact_type"] = reference.artifact_type
        if reference.artifact_id:
            metadata["artifact_id"] = str(reference.artifact_id)
        return EducationalContext(
            tenant_id=values["tenant_id"],
            resolution_status=status,  # type: ignore[arg-type]
            academic_year_id=values.get("academic_year_id"),
            academic_year=values.get("academic_year"),
            board=values.get("board"),
            curriculum=values.get("curriculum"),
            curriculum_version=values.get("curriculum_version"),
            grade=values.get("grade"),
            section=values.get("section"),
            subject=values.get("subject"),
            curriculum_pack_id=values.get("curriculum_pack_id"),
            educational_identity_id=values.get("educational_identity_id"),
            chapter=values.get("chapter"),
            topic=values.get("topic"),
            concepts=_tuple(values.get("concepts")),
            competencies=_tuple(values.get("competencies")),
            learning_objectives=_tuple(values.get("learning_objectives")),
            assessment_mode=values.get("assessment_mode"),
            language_medium=values.get("language_medium"),
            evidence_posture=values.get("evidence_posture"),
            field_sources=dict(builder.field_sources),
            conflicts=tuple(builder.conflicts),
            ambiguities=tuple(builder.ambiguities),
            metadata=metadata,
            provenance=EducationalContextProvenance(
                source="passive_context_resolver",
                source_id=_first_present(
                    values.get("educational_identity_id"),
                    values.get("curriculum_pack_id"),
                    reference.artifact_id,
                ),
                source_version=values.get("curriculum_version"),
                resolved_from=reference.resolution_kind,
                metadata={"passive": True},
            ),
        )

    @staticmethod
    def _resolution_status(builder: _ContextBuilder) -> str:
        if builder.ambiguities:
            return "ambiguous"
        if builder.conflicts:
            return "resolved_with_conflicts"
        return "resolved"


def _has_identity_reference(reference: EducationalContextReference) -> bool:
    return any(
        value is not None
        for value in (
            reference.pack_id,
            reference.chapter_id,
            reference.topic_id,
            reference.concept_id,
            reference.learning_outcome_id,
        )
    )


def _has_minimum_context(values: dict[str, Any]) -> bool:
    return any(
        not _empty(values.get(field))
        for field in (
            "educational_identity_id",
            "curriculum_pack_id",
            "board",
            "grade",
            "subject",
            "chapter",
            "topic",
            "assessment_mode",
        )
    )


def _cache_key(reference: EducationalContextReference) -> str:
    payload = reference.model_dump(mode="json", exclude_none=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _empty(value: Any) -> bool:
    return value is None or value == "" or value == () or value == []


def _equivalent(left: Any, right: Any) -> bool:
    return _normalize(left) == _normalize(right)


def _normalize(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, str):
        return " ".join(value.casefold().split())
    if isinstance(value, (list, tuple)):
        return tuple(_normalize(item) for item in value)
    return value


def _display(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return (str(value),)


def _uuid_from_metadata(value: Any) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return None
    return None


def _first_present(*values: Any) -> str | None:
    for value in values:
        if not _empty(value):
            return str(value)
    return None
