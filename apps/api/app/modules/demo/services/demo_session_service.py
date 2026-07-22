"""Demo session orchestration — provision, renew, expiry sweep, cleanup (Stage 2B)."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.auth.services.auth_service import AuthService
from app.modules.demo import ONBOARDING_PATH, TENANT_KIND_PROSPECT_DEMO
from app.modules.demo.schemas.demo import DemoSessionOut
from app.modules.demo.services.cleanup_service import TenantCleanupService
from app.modules.demo.services.provisioning_service import TenantProvisioningService

logger = structlog.get_logger()
settings = get_settings()


class DemoSessionError(ValueError):
    """Demo session cannot be created or renewed."""


class DemoSessionService:
    def __init__(self, db: AsyncSession, redis=None) -> None:
        self.db = db
        self.redis = redis

    async def _issue_demo_tokens(self, school: School, principal: User) -> tuple[str, str]:
        auth = AuthService(self.db, self.redis)
        expires_at = school.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return await auth.issue_tokens(
            principal,
            refresh_expires_at=expires_at,
            extra_access_claims={"demo": True},
        )

    async def create_session(
        self, *, display_name: str | None = None
    ) -> tuple[DemoSessionOut, str]:
        """Returns (response, refresh_token) for HttpOnly cookie."""
        provisioner = TenantProvisioningService(self.db)
        result = await provisioner.provision_prospect_session(display_name=display_name)
        access_token, refresh_token = await self._issue_demo_tokens(
            result.school, result.principal
        )
        out = DemoSessionOut(
            tenant_slug=result.school.tenant_slug,
            school_id=str(result.school.id),
            expires_at=result.expires_at,
            access_token=access_token,
            session_token=result.raw_session_token,
            onboarding_path=ONBOARDING_PATH,
            school_name=result.school.name,
        )
        return out, refresh_token

    async def renew_session(
        self, *, tenant_slug: str, session_token: str
    ) -> tuple[DemoSessionOut, str]:
        """Exchange a demo session token for fresh JWTs (72h school window)."""
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        row = await self.db.execute(
            select(School).where(
                School.tenant_slug == tenant_slug,
                School.demo_session_token_hash == token_hash,
                School.tenant_kind == TENANT_KIND_PROSPECT_DEMO,
                School.is_active.is_(True),
            )
        )
        school = row.scalar_one_or_none()
        if school is None:
            raise DemoSessionError("Invalid or expired demo session")
        if school.expires_at is None or school.expires_at <= now:
            raise DemoSessionError("Demo session expired")

        principal = (
            await self.db.execute(
                select(User).where(
                    User.school_id == school.id,
                    User.username == "principal",
                    User.role == UserRole.SUPER_ADMIN,
                    User.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if principal is None:
            raise DemoSessionError("Demo principal account unavailable")

        access_token, refresh_token = await self._issue_demo_tokens(school, principal)
        out = DemoSessionOut(
            tenant_slug=school.tenant_slug,
            school_id=str(school.id),
            expires_at=school.expires_at,
            access_token=access_token,
            session_token=session_token,
            onboarding_path=ONBOARDING_PATH,
            school_name=school.name,
        )
        return out, refresh_token

    async def sweep_expired(self, *, enqueue_cleanup: bool = True) -> list[str]:
        """Deactivate expired prospect tenants and purge (or enqueue purge)."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(School.id, School.tenant_slug).where(
                School.tenant_kind == TENANT_KIND_PROSPECT_DEMO,
                School.is_active.is_(True),
                School.expires_at.isnot(None),
                School.expires_at <= now,
            )
        )
        expired = result.all()
        if not expired:
            return []

        school_ids = [row[0] for row in expired]
        await self.db.execute(
            update(School)
            .where(School.id.in_(school_ids))
            .values(is_active=False, updated_at=now)
        )
        await self.db.commit()

        swept: list[str] = []
        for school_id, slug in expired:
            if enqueue_cleanup:
                try:
                    await self._enqueue_cleanup(school_id)
                except Exception:
                    logger.exception("demo_cleanup_enqueue_failed", school_id=str(school_id))
                    cleanup = TenantCleanupService(self.db, redis=self.redis)
                    await cleanup.purge_prospect_tenant(school_id)
            else:
                cleanup = TenantCleanupService(self.db, redis=self.redis)
                await cleanup.purge_prospect_tenant(school_id)
            swept.append(slug)
            logger.info("prospect_tenant_expired", school_id=str(school_id), tenant_slug=slug)
        return swept

    async def _enqueue_cleanup(self, school_id: uuid.UUID) -> None:
        from app.core.jobs.queue import enqueue

        await enqueue(
            self.db,
            task="tenant_cleanup",
            params={"school_id": str(school_id)},
            school_id=school_id,
        )
        await self.db.commit()

    async def purge_now(
        self, school_id: uuid.UUID, *, exclude_job_id: uuid.UUID | None = None
    ) -> dict:
        cleanup = TenantCleanupService(self.db, redis=self.redis)
        return await cleanup.purge_prospect_tenant(school_id, exclude_job_id=exclude_job_id)


async def assert_demo_school_active(db: AsyncSession, school_id: uuid.UUID) -> None:
    """Reject refresh/renew when a prospect demo school has expired."""
    school = await db.get(School, school_id)
    if school is None or not school.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="School unavailable")
    if school.tenant_kind != TENANT_KIND_PROSPECT_DEMO:
        return
    if school.expires_at is not None and school.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Demo session expired. Start a new demo to continue.",
        )
