"""Stable transient Educational Knowledge Graph proposal IDs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.modules.eui.schemas.educational_graph import (
    EducationalGraphRelationshipReference,
)


def stable_educational_graph_proposal_id(
    reference: EducationalGraphRelationshipReference,
    *,
    relationship_category: str,
    status: str,
    target_reference_id: str | None,
) -> str:
    """Generate a deterministic transient proposal ID.

    Phase 5 does not persist proposal IDs. The hash excludes free-text content
    from KAI candidates because those candidates already expose deterministic
    candidate IDs and normalized content hashes.
    """

    payload = {
        "reference": _safe_reference_payload(reference),
        "relationship_category": relationship_category,
        "status": status,
        "target_reference_id": target_reference_id,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = _sha256(serialized)[:20]
    return f"ekg-proposal://{_slug(relationship_category)}/{digest}"


def _safe_reference_payload(reference: EducationalGraphRelationshipReference) -> dict[str, Any]:
    payload = reference.model_dump(
        mode="json",
        exclude_none=True,
        exclude={
            "kai_candidate": {"extracted_text"},
        },
    )
    candidate = reference.kai_candidate
    if candidate is not None:
        payload["kai_candidate"] = {
            **payload.get("kai_candidate", {}),
            "id": candidate.id,
            "review_status": candidate.review_status,
            "source_type": candidate.source_type,
            "educational_identity_id": candidate.educational_identity_id,
        }
    return payload


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _slug(value: Any) -> str:
    normalized = str(value).strip().casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-") or "unknown"
