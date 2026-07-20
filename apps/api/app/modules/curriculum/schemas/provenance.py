"""Provenance helpers for curriculum-grounded AI outputs."""
from __future__ import annotations

from datetime import date, datetime


def provenance_from_sources(
    sources: list[dict] | None,
    *,
    pack_id: str | None = None,
    grounded: bool = False,
    created_at: datetime | date | None = None,
) -> dict:
    """Extract pack provenance for API/UI from grounding sources."""
    src = (sources or [{}])[0] if sources else {}
    return {
        "pack_id": pack_id or src.get("pack_id"),
        "pack_status": src.get("pack_status"),
        "pack_version": src.get("pack_version"),
        "grounded": grounded or bool(pack_id or src.get("pack_id")),
        "grounded_at": created_at,
    }
