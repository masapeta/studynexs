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


def mask_mobile(value: str | None) -> str | None:
    """Mask a phone number for logs, keeping only the last 4 digits (e.g. +91987…3210 → ******3210).

    Preserves a leading '+' so the value is still recognizable as a phone number without
    exposing the subscriber. Use everywhere a mobile number would otherwise reach logs.
    """
    if not value:
        return None
    cleaned = value.strip()
    plus = "+" if cleaned.startswith("+") else ""
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) <= 4:
        return plus + "*" * len(digits)
    return plus + "*" * (len(digits) - 4) + digits[-4:]


def mask_email(value: str | None) -> str | None:
    """Mask an email for logs: keep the first char of the local part and the domain
    (e.g. john.doe@example.com → j***@example.com). Falls back to full mask if malformed."""
    if not value:
        return None
    cleaned = value.strip()
    if "@" not in cleaned:
        return mask_id_number(cleaned)
    local, _, domain = cleaned.partition("@")
    if not local:
        return "***@" + domain
    return f"{local[0]}***@{domain}"
