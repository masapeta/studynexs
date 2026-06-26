"""Map LLM/provider failures to safe HTTP responses — no stack traces to clients."""
from __future__ import annotations

import structlog
from fastapi import HTTPException, status

logger = structlog.get_logger()

_TIMEOUT_TYPE_NAMES = frozenset({
    "APITimeoutError",
    "TimeoutError",
    "ReadTimeout",
    "ConnectTimeout",
    "WriteTimeout",
})


def raise_http_for_llm_error(
    exc: BaseException,
    *,
    log_event: str,
    timeout_detail: str = "AI generation timed out. Please try again.",
    generic_detail: str = "AI generation failed. Please try again later.",
) -> None:
    """Normalize provider/SDK failures into 400/503/504 responses."""
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if isinstance(exc, ModuleNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='AI provider SDK not installed. Run: pip install -e ".[ai]"',
        ) from exc
    if isinstance(exc, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if type(exc).__name__ in _TIMEOUT_TYPE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=timeout_detail,
        ) from exc
    logger.exception(log_event)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=generic_detail,
    ) from exc
