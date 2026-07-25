"""
HTTP metrics middleware — structured request timing for soak tests and APM.
"""
from __future__ import annotations

import re
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.platform_metrics import platform_metrics

logger = structlog.get_logger()

_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def normalize_path(path: str) -> str:
    """Collapse UUIDs so metrics do not explode per entity."""
    return _UUID.sub("{id}", path)


def request_id_from(request: Request) -> str:
    raw = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
    if raw and raw.strip():
        return raw.strip()[:128]
    return str(uuid.uuid4())


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request_id_from(request)
        request.state.request_id = request_id
        start = time.perf_counter()
        route = normalize_path(request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            platform_metrics.record_http_request(
                method=request.method,
                path=route,
                status_code=500,
                duration_ms=duration_ms,
            )
            logger.exception(
                "http_request_failed",
                request_id=request_id,
                method=request.method,
                path=route,
                duration_ms=duration_ms,
                tenant_slug=getattr(request.state, "tenant_slug", None),
            )
            raise
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        platform_metrics.record_http_request(
            method=request.method,
            path=route,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        current_user = getattr(request.state, "current_user", None)
        role = getattr(current_user, "role", None)
        if hasattr(role, "value"):
            role = role.value

        logger.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=route,
            status=response.status_code,
            duration_ms=duration_ms,
            tenant_slug=getattr(request.state, "tenant_slug", None),
            school_id=str(getattr(current_user, "school_id", "")) or None,
            user_id=str(getattr(current_user, "id", "")) or None,
            role=role,
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response
