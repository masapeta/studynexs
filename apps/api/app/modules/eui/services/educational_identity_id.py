"""Stable Educational Identity ID generation."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote

_SLUG_CLEAN_RE = re.compile(r"[^\w\s-]", re.UNICODE)
_SPACE_RE = re.compile(r"[\s_]+", re.UNICODE)
_GRADE_RE = re.compile(r"(?:grade|class|standard|std)?\s*(\d{1,2})", re.IGNORECASE)


def stable_identity_id(
    *,
    board: str,
    curriculum: str,
    curriculum_version: str,
    grade: str,
    subject: str,
    chapter_number: str | None = None,
    chapter: str | None = None,
    topic: str | None = None,
    concept: str | None = None,
    learning_objective: str | None = None,
    competency: str | None = None,
) -> str:
    """Build a deterministic ``ei://`` identifier from curriculum identity parts."""

    segments = [
        "ei:",
        "",
        _slug(board),
        _slug(curriculum),
        _slug(curriculum_version),
        _grade_segment(grade),
        _slug(subject),
    ]
    chapter_segment = _chapter_segment(chapter_number=chapter_number, chapter=chapter)
    if chapter_segment:
        segments.append(chapter_segment)
    if topic:
        segments.append(f"topic-{_slug(topic)}")
    if concept:
        segments.append(f"concept-{_slug(concept)}")
    if learning_objective:
        segments.append(f"lo-{_slug(learning_objective)}")
    if competency:
        segments.append(f"competency-{_slug(competency)}")
    return "/".join(segments)


def identity_alias(*parts: object) -> str:
    """Build a stable lookup alias for registry keys."""

    return ":".join(_slug(str(part)) for part in parts if part is not None and str(part) != "")


def _chapter_segment(*, chapter_number: str | None, chapter: str | None) -> str | None:
    if chapter_number and chapter_number.strip():
        stripped = chapter_number.strip()
        if stripped.isdigit():
            return f"ch{int(stripped):02d}"
        return f"ch-{_slug(stripped)}"
    if chapter and chapter.strip():
        return f"chapter-{_slug(chapter)}"
    return None


def _grade_segment(grade: str) -> str:
    match = _GRADE_RE.search(grade.strip())
    if match:
        return f"g{int(match.group(1))}"
    return _slug(grade)


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").strip().lower()
    cleaned = _SLUG_CLEAN_RE.sub("", normalized)
    slug = _SPACE_RE.sub("-", cleaned).strip("-")
    return quote(slug or "unknown", safe="-")
