"""Stable transient Trust Report IDs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def stable_trust_report_id(
    *,
    subject_type: str,
    subject_ref: str,
    payload: dict[str, Any],
) -> str:
    """Generate a deterministic transient Trust Report ID."""

    serialized = json.dumps(
        {
            "subject_type": subject_type,
            "subject_ref": subject_ref,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:20]
    return f"trust-report://{_slug(subject_type)}/{digest}"


def _slug(value: Any) -> str:
    normalized = str(value).strip().casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-") or "unknown"
