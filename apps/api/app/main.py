"""
StudyNexs Platform — FastAPI Application Entry Point
Creates the app, mounts CORS, routers, health checks.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.core.config import Environment, get_settings

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    from app.core.otel import setup_opentelemetry, shutdown_opentelemetry

    setup_opentelemetry(settings)
    logger.info("StudyNexs API starting", environment=settings.ENVIRONMENT.value)

    from app.modules.tutor.services.tts_service import (
        default_tts_voice,
        resolve_tts_backend,
        tts_enabled,
    )

    tts_backend = resolve_tts_backend()
    logger.info(
        "tutor_tts_config",
        backend=tts_backend,
        voice=default_tts_voice(),
        enabled=tts_enabled(),
        provider=settings.TUTOR_TTS_PROVIDER,
    )
    if settings.TUTOR_TTS_PROVIDER.strip().lower() in ("edge", "auto") and not tts_enabled():
        logger.warning(
            "tutor_tts_unavailable",
            hint="Install edge-tts in this Python env: python -m pip install edge-tts",
        )

    outbox_task: asyncio.Task | None = None
    if settings.OUTBOX_WORKER_ENABLED and settings.ENVIRONMENT not in (Environment.TESTING,):
        # Register outbox handlers (side effect on import)
        import app.workers.outbox_worker  # noqa: F401
        from app.workers.outbox_worker import run_worker

        outbox_task = asyncio.create_task(
            run_worker(poll_interval=settings.OUTBOX_POLL_INTERVAL_SECONDS)
        )
        logger.info("outbox_worker_embedded_started")

    yield

    if outbox_task:
        outbox_task.cancel()
        with suppress(asyncio.CancelledError):
            await outbox_task
        logger.info("outbox_worker_embedded_stopped")

    logger.info("StudyNexs API shutting down")
    shutdown_opentelemetry()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    from app.core.otel import instrument_fastapi

    instrument_fastapi(app, settings)

    # ── CORS ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # BaseHTTPMiddleware breaks async DB under pytest; skip in testing.
    if settings.ENVIRONMENT != Environment.TESTING:
        from app.core.ai_telemetry_middleware import AITelemetryMiddleware
        from app.core.audit_middleware import AuditMiddleware
        from app.core.metrics_middleware import MetricsMiddleware
        from app.core.tenant_middleware import TenantMiddleware

        app.add_middleware(AITelemetryMiddleware)
        app.add_middleware(AuditMiddleware)
        app.add_middleware(TenantMiddleware)
        app.add_middleware(MetricsMiddleware)

    # ── Health Checks ────────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "healthy", "service": settings.APP_NAME}

    @app.get("/ready", tags=["system"])
    async def readiness():
        """Readiness probe — checks DB and Redis connectivity."""
        from app.core.database import engine
        from app.core.dependencies import get_redis

        checks = {}
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e}"

        try:
            r = await get_redis()
            await r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        all_ok = all(v == "ok" for v in checks.values())
        return {"status": "ready" if all_ok else "degraded", "checks": checks}

    @app.get("/metrics", tags=["system"])
    async def prometheus_metrics(request: Request):
        """Prometheus scrape endpoint — LLM counters, latency histograms, fallback rates."""
        from app.modules.ai.telemetry import ai_metrics

        token = settings.METRICS_TOKEN
        if settings.is_production and not token:
            raise HTTPException(status_code=404, detail="Not found")
        if token:
            auth = request.headers.get("Authorization", "")
            header = request.headers.get("X-Metrics-Token", "")
            if auth != f"Bearer {token}" and header != token:
                raise HTTPException(status_code=401, detail="Unauthorized")

        return PlainTextResponse(
            ai_metrics.prometheus_text(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    # ── Exception handlers ───────────────────────────────────────
    from sqlalchemy.exc import IntegrityError

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Map DB constraint violations to 409 instead of a 500."""
        structlog.get_logger().warning("integrity_error", path=str(request.url.path))
        return JSONResponse(
            status_code=409,
            content={
                "detail": "This conflicts with existing data (duplicate or constraint violation)."
            },
        )

    # ── Mount Routers ────────────────────────────────────────────
    prefix = settings.API_V1_PREFIX

    from app.modules.academic.endpoints.academic import router as academic_router
    from app.modules.ai.endpoints.ai import router as ai_router
    from app.modules.attendance.endpoints.attendance import router as attendance_router
    from app.modules.auth.endpoints.auth import router as auth_router
    from app.modules.communications.endpoints.notice import router as notice_router
    from app.modules.examinations.endpoints.exam import router as exam_router
    from app.modules.fees.endpoints.fee import router as fee_router
    from app.modules.files.endpoints.file import router as file_router
    from app.modules.jobs.endpoints.job import router as jobs_router
    from app.modules.mastery.endpoints.mastery import router as mastery_router
    from app.modules.notifications.endpoints.notification import router as notif_router
    from app.modules.portal.endpoints.portal import router as portal_router
    from app.modules.school.endpoints.school import router as school_router
    from app.modules.school_ops.endpoints.ops import router as ops_router
    from app.modules.timetable.endpoints.timetable import router as timetable_router
    from app.modules.users.endpoints.users import router as users_router

    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{prefix}/users", tags=["users"])
    app.include_router(academic_router, prefix=f"{prefix}/academic", tags=["academic"])
    app.include_router(attendance_router, prefix=f"{prefix}/attendance", tags=["attendance"])
    app.include_router(exam_router, prefix=f"{prefix}/exams", tags=["examinations"])
    app.include_router(fee_router, prefix=f"{prefix}/fees", tags=["fees"])
    app.include_router(timetable_router, prefix=f"{prefix}/timetable", tags=["timetable"])
    app.include_router(notice_router, prefix=f"{prefix}/notices", tags=["communications"])
    app.include_router(ops_router, prefix=f"{prefix}/ops", tags=["school-operations"])
    app.include_router(notif_router, prefix=f"{prefix}/notifications", tags=["notifications"])
    app.include_router(file_router, prefix=f"{prefix}/files", tags=["files"])
    app.include_router(jobs_router, prefix=f"{prefix}/jobs", tags=["jobs"])
    app.include_router(ai_router, prefix=f"{prefix}/ai", tags=["ai"])
    app.include_router(school_router, prefix=f"{prefix}/school", tags=["school"])
    app.include_router(mastery_router, prefix=f"{prefix}/mastery", tags=["mastery"])

    from app.modules.curriculum.endpoints.pack import router as curriculum_pack_router
    from app.modules.curriculum.endpoints.ingest import router as curriculum_ingest_router
    from app.modules.curriculum.endpoints.graph import router as curriculum_graph_router
    from app.modules.curriculum.endpoints.concept_card import router as concept_card_router
    from app.modules.curriculum.endpoints.content_review import router as content_review_router
    from app.modules.curriculum.endpoints.rag import router as curriculum_rag_router

    app.include_router(curriculum_pack_router, prefix=f"{prefix}/curriculum", tags=["curriculum"])
    app.include_router(curriculum_ingest_router, prefix=f"{prefix}/curriculum", tags=["curriculum"])
    app.include_router(curriculum_graph_router, prefix=f"{prefix}/curriculum", tags=["curriculum"])
    app.include_router(concept_card_router, prefix=f"{prefix}/curriculum", tags=["curriculum"])
    app.include_router(content_review_router, prefix=f"{prefix}/curriculum", tags=["curriculum"])
    app.include_router(curriculum_rag_router, prefix=f"{prefix}/curriculum", tags=["curriculum"])
    app.include_router(portal_router, prefix=f"{prefix}/portal", tags=["portal"])

    from app.modules.tutor.endpoints.tutor import router as tutor_router

    app.include_router(tutor_router, prefix=f"{prefix}/tutor", tags=["tutor"])

    from app.modules.curriculum.endpoints.lesson_plan import router as lesson_plan_router
    from app.modules.dashboard.endpoints.dashboard import router as dashboard_router
    from app.modules.platform.endpoints.engineering import router as platform_router

    app.include_router(dashboard_router, prefix=f"{prefix}/dashboard", tags=["dashboard"])
    app.include_router(platform_router, prefix=f"{prefix}/platform", tags=["platform"])
    app.include_router(lesson_plan_router, prefix=f"{prefix}/lesson-plans", tags=["curriculum"])

    return app


app = create_app()
