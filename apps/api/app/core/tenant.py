"""
StudyNexs Platform — Tenant Resolution Middleware
Resolves subdomain slugs (e.g., sia.studynexs.com → school_id) to tenant context.
Platform hosts (api, app, demo, …) never derive a tenant from the hostname — see URL_ARCHITECTURE.md.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings


def _reserved_subdomains() -> frozenset[str]:
    return frozenset(s.lower() for s in get_settings().TENANT_RESERVED_SUBDOMAINS)


def subdomain_slug_from_host(hostname: str, base_domain: str) -> str | None:
    """
    Extract a school tenant slug from hostname, or None if the host is not a tenant host.

    Returns None for apex hosts, platform reserved subdomains (api, app, …), and non-matching domains.
    """
    host = hostname.split(":")[0].lower()
    base = base_domain.lower()
    if not host.endswith(f".{base}"):
        return None
    slug = host.removesuffix(f".{base}")
    if not slug or slug in _reserved_subdomains():
        return None
    return slug


def extract_tenant_slug(request: Request) -> str:
    """
    Extract tenant slug from:
    1. School subdomain: dps.studynexs.com → "dps" (skipped for platform hosts)
    2. Header: X-Tenant-Slug (required on api.studynexs.com and other platform API hosts)
    3. Default: settings.DEFAULT_TENANT_SLUG (development only)
    """
    hostname = request.headers.get("host", "").split(":")[0]
    settings = get_settings()
    base_domain = settings.TENANT_BASE_DOMAIN

    slug_from_host = subdomain_slug_from_host(hostname, base_domain)
    if slug_from_host:
        return slug_from_host

    header_slug = request.headers.get("x-tenant-slug", "").strip()
    if header_slug:
        return header_slug

    if settings.is_development:
        return settings.DEFAULT_TENANT_SLUG

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to determine school tenant. Use a school subdomain or X-Tenant-Slug header.",
    )


async def resolve_tenant(slug: str, db: AsyncSession) -> str:
    """
    Resolve a tenant slug to a school_id (UUID).
    Raises 404 if slug is unknown.
    Returns school_id as string.
    """
    from app.db.models.school import School

    result = await db.execute(
        select(School.id, School.expires_at).where(
            School.tenant_slug == slug, School.is_active.is_(True)
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School not found for tenant: {slug}",
        )

    school_id, expires_at = row
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Demo session expired. Start a new demo to continue.",
        )

    return str(school_id)


async def resolve_auth_school_id(request: Request, db: AsyncSession) -> uuid.UUID:
    """
    Resolve school for unauthenticated auth routes (login / OTP).
    Uses X-Tenant-Slug in tests and dev; subdomain in production.
    """
    settings = get_settings()
    if settings.ENVIRONMENT == Environment.TESTING:
        slug = request.headers.get("x-tenant-slug") or settings.DEFAULT_TENANT_SLUG
    else:
        slug = getattr(request.state, "tenant_slug", None) or extract_tenant_slug(request)
    school_id = await resolve_tenant(slug, db)
    return uuid.UUID(school_id)


async def validate_tenant_school_match(
    request: Request, db: AsyncSession, school_id: str
) -> None:
    """Ensure the user's school matches the request tenant (subdomain or header)."""
    settings = get_settings()
    if settings.ENVIRONMENT == Environment.TESTING:
        return
    if settings.is_development and not request.headers.get("x-tenant-slug"):
        return

    slug = getattr(request.state, "tenant_slug", None) or extract_tenant_slug(request)
    expected_school_id = await resolve_tenant(slug, db)
    if expected_school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not valid for this school tenant",
        )
