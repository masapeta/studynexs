"""
Audit Logging Middleware — auto-logs all mutating API calls.
Captures: who, what, when, from where, on which school.
"""

import json
import time
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import Request, Response
from sqlalchemy import insert
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import Environment, get_settings
from app.core.database import async_session_factory
from app.db.models.audit import AuditLog

logger = structlog.get_logger()
settings = get_settings()

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip non-mutating and system routes
        if request.method not in MUTATING_METHODS:
            return await call_next(request)

        if any(request.url.path.startswith(p) for p in SKIP_PATHS):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Extract user info from request state (set by auth middleware)
        user_id = None
        school_id = None
        role = None

        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            user_id = getattr(user, "id", None)
            school_id = getattr(user, "school_id", None)
            role = getattr(user, "role", None)

        # Build action from method + path
        action = f"{request.method} {request.url.path}"

        # Log to structured logger
        logger.info(
            "audit",
            action=action,
            user_id=user_id,
            school_id=school_id,
            role=role,
            status=response.status_code,
            duration_ms=duration_ms,
            ip=request.client.host if request.client else None,
        )

        # Persist to DB (skipped in tests — separate session conflicts with pytest DB override)
        if settings.ENVIRONMENT != Environment.TESTING and user_id and school_id:
            try:
                async with async_session_factory() as session:
                    session.add(AuditLog(
                        school_id=uuid.UUID(school_id) if isinstance(school_id, str) else school_id,
                        user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
                        action=action[:200],
                        resource_type=request.url.path.split("/")[-2] if "/" in request.url.path else "unknown",
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent", "")[:300],
                        details={"status": response.status_code, "duration_ms": duration_ms},
                    ))
                    await session.commit()
            except Exception as e:
                logger.warning("audit_persist_failed", error=str(e))

        return response
