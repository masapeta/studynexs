"""Public prospect demo session API (Stage 2B)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import check_rate_limit, get_redis
from app.core.turnstile import verify_turnstile_token
from app.modules.auth.cookie_util import set_refresh_cookie
from app.modules.auth.endpoints.auth import _get_client_ip
from app.modules.demo.schemas.demo import (
    DemoSessionCreateRequest,
    DemoSessionOut,
    DemoSessionRenewRequest,
)
from app.modules.demo.services.demo_session_service import DemoSessionError, DemoSessionService
from app.modules.demo.services.provisioning_service import DemoProvisioningError
from app.shared.schemas.common import APIResponse

router = APIRouter(route_class=CommitOnSuccessRoute)
settings = get_settings()


async def _require_turnstile(request: Request, token: str | None) -> None:
    if not settings.demo_turnstile_required:
        return
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot verification required",
        )
    client_ip = _get_client_ip(request)
    if not await verify_turnstile_token(token, remote_ip=client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bot verification failed",
        )


@router.post(
    "/sessions",
    response_model=APIResponse[DemoSessionOut],
    status_code=201,
    summary="Provision an isolated prospect demo tenant",
)
async def create_demo_session(
    request: Request,
    response: Response,
    body: DemoSessionCreateRequest | None = None,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    if not settings.demo_provisioning_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo provisioning is not available",
        )

    await _require_turnstile(request, body.turnstile_token if body else None)

    client_ip = _get_client_ip(request)
    await check_rate_limit(
        key=f"demo:provision:{client_ip}",
        max_attempts=settings.DEMO_PROVISION_RATE_LIMIT_MAX,
        window_seconds=settings.DEMO_PROVISION_RATE_LIMIT_WINDOW_SECONDS,
        r=redis,
    )

    service = DemoSessionService(db, redis=redis)
    try:
        session, refresh_token = await service.create_session(
            display_name=body.display_name if body else None,
        )
    except DemoProvisioningError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
            if "capacity" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    set_refresh_cookie(response, refresh_token)
    return APIResponse(data=session)


@router.post(
    "/sessions/renew",
    response_model=APIResponse[DemoSessionOut],
    summary="Renew demo access using the session token (72h window)",
)
async def renew_demo_session(
    request: Request,
    response: Response,
    body: DemoSessionRenewRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    tenant_slug = request.headers.get("x-tenant-slug", "").strip()
    if not tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Slug header required",
        )

    client_ip = _get_client_ip(request)
    await check_rate_limit(
        key=f"demo:renew:{client_ip}:{tenant_slug}",
        max_attempts=settings.DEMO_PROVISION_RATE_LIMIT_MAX * 4,
        window_seconds=settings.DEMO_PROVISION_RATE_LIMIT_WINDOW_SECONDS,
        r=redis,
    )

    service = DemoSessionService(db, redis=redis)
    try:
        session, refresh_token = await service.renew_session(
            tenant_slug=tenant_slug,
            session_token=body.session_token,
        )
    except DemoSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE
            if "expired" in str(exc).lower()
            else status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    set_refresh_cookie(response, refresh_token)
    return APIResponse(data=session)
