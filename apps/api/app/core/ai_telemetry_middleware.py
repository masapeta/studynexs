"""Bind request correlation IDs and route path into AI telemetry context."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.otel import current_trace_id
from app.modules.ai.telemetry import bind_ai_context, reset_ai_context


class AITelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = (
            getattr(request.state, "request_id", None)
            or request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
        )
        bind_ai_context(
            request_id=request_id,
            endpoint=f"{request.method} {request.url.path}",
        )
        trace_id = current_trace_id()
        if trace_id:
            bind_ai_context(request_id=trace_id)
        try:
            return await call_next(request)
        finally:
            reset_ai_context()
