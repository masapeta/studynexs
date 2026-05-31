"""
StudyNexs Platform — Tenant Resolution Middleware
Resolves subdomain slugs (e.g., sia.studynexs.com → school_id) to tenant context.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings

settings = get_settings()


def extract_tenant_slug(request: Request) -> str:
    """
    Extract tenant slug from:
    1. Subdomain: sia.studynexs.com → "sia"
    2. Header: X-Tenant-Slug (fallback for local dev / API clients)
    3. Default: settings.DEFAULT_TENANT_SLUG (development only)
    """
    host = request.headers.get("host", "")

    # Strip port if present (e.g., "sia.localhost:3000" → "sia.localhost")
    hostname = host.split(":")[0]

    # Check for subdomain pattern: slug.studynexs.com
    base_domain = settings.TENANT_BASE_DOMAIN
    if hostname.endswith(f".{base_domain}"):
        slug = hostname.removesuffix(f".{base_domain}")
        if slug and slug != "www":
            return slug

    # Fallback: explicit header
    header_slug = request.headers.get("x-tenant-slug", "")
    if header_slug:
        return header_slug

    # Development fallback
    if settings.is_development:
        return settings.DEFAULT_TENANT_SLUG

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to determine school tenant. Use subdomain or X-Tenant-Slug header.",
    )


async def resolve_tenant(slug: str, db: AsyncSession) -> str:
    """
    Resolve a tenant slug to a school_id (UUID).
    Raises 404 if slug is unknown.
    Returns school_id as string.
    """
    from app.db.models.school import School

    result = await db.execute(
        select(School.id).where(School.tenant_slug == slug, School.is_active == True)
    )
    school_id = result.scalar_one_or_none()

    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School not found for tenant: {slug}",
        )

    return str(school_id)


async def resolve_auth_school_id(request: Request, db: AsyncSession) -> uuid.UUID:
    """
    Resolve school for unauthenticated auth routes (login / OTP).
    Uses X-Tenant-Slug in tests and dev; subdomain in production.
    """
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
