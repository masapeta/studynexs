"""PII masking helpers — never log or expose full values in list/summary APIs."""
from __future__ import annotations

import re


def mask_aadhaar(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) != 12:
        return "****"
    return f"XXXX-XXXX-{digits[-4:]}"


def mask_id_number(value: str | None, *, visible_tail: int = 4) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if len(cleaned) <= visible_tail:
        return "*" * len(cleaned)
    return "*" * (len(cleaned) - visible_tail) + cleaned[-visible_tail:]
