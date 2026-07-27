"""Stable transient KAI candidate IDs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference


def stable_kai_candidate_id(reference: KnowledgeAcquisitionInputReference) -> str:
    """Generate a deterministic transient KAI candidate ID.

    The hash includes a digest of supplied text, not raw text. Phase 4 does not
    persist IDs; this is for deterministic passive evidence and tests only.
    """

    payload = reference.model_dump(mode="json", exclude_none=True)
    supplied_text = payload.pop("supplied_extracted_text", None)
    if supplied_text is not None:
        payload["supplied_extracted_text_sha256"] = _sha256(str(supplied_text))
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = _sha256(serialized)[:20]
    source = _slug(reference.source_type)
    return f"kai://{source}/{digest}"


def content_hash(value: str | None) -> str | None:
    if value is None:
        return None
    return _sha256(value)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _slug(value: Any) -> str:
    normalized = str(value).strip().casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-") or "unknown"
