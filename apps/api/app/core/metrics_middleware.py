"""
HTTP metrics middleware — structured request timing for soak tests and APM.
"""
from __future__ import annotations

import re
import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def normalize_path(path: str) -> str:
    """Collapse UUIDs so metrics do not explode per entity."""
    return _UUID.sub("{id}", path)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        route = normalize_path(request.url.path)

        logger.info(
            "http_request",
            method=request.method,
            path=route,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response
