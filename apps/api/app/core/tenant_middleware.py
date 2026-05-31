"""
Tenant context middleware — resolves subdomain/header slug for downstream validation.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.tenant import extract_tenant_slug

SKIP_PREFIXES = ("/health", "/ready", "/docs", "/redoc", "/openapi.json")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        try:
            request.state.tenant_slug = extract_tenant_slug(request)
        except Exception:
            request.state.tenant_slug = None

        return await call_next(request)
