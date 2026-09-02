"""Customer-safe API error details.

Preserves concise business messages but masks technical/internal exception text so
it never reaches end users.
"""

from __future__ import annotations

import re

_TECHNICAL_DETAIL = re.compile(
    r"traceback|exception|stack\s*trace|sqlalchemy|asyncpg|psycopg|fastapi|uvicorn|"
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|:8000|keyerror|typeerror|runtimeerror|"
    r"jsondecodeerror|cannot\s+load\s+library|libgobject|weasyprint|module\s+not\s+found|"
    r"file\s+\"|line\s+\d+",
    re.IGNORECASE,
)


def user_error_detail(exc: Exception | str | None, *, fallback: str, max_length: int = 220) -> str:
    """Return a customer-safe message for API responses.

    - Keeps short domain-safe validation messages (e.g. "Question is required").
    - Replaces technical/internal exception text with ``fallback``.
    """
    text = str(exc or "").strip()
    if not text:
        return fallback
    if len(text) > max_length:
        return fallback
    if _TECHNICAL_DETAIL.search(text):
        return fallback
    return text
