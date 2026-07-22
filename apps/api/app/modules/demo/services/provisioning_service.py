"""Minimal prospect tenant provisioning — reuses Stage 2A academic shell, no approved pack."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.services.ai_credits import DEFAULT_AI_BUDGET
from app.modules.demo import ONBOARDING_PATH, TENANT_KIND_PROSPECT_DEMO

logger = structlog.get_logger()
settings = get_settings()

_RESERVED_SLUGS = frozenset(
    s.lower()
    for s in (
        *settings.TENANT_RESERVED_SUBDOMAINS,
        *settings.DEMO_PROTECTED_TENANT_SLUGS,
    )
)


class DemoProvisioningError(ValueError):
    """Visitor cannot receive a new demo tenant."""


@dataclass
class ProspectProvisionResult:
    school: School
    principal: User
    raw_session_token: str
    expires_at: datetime


class TenantProvisioningService:
    """Create an isolated prospect school with principal auth — no duplicate AI stack."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _active_prospect_count(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(School)
            .where(
                School.tenant_kind == TENANT_KIND_PROSPECT_DEMO,
                School.is_active.is_(True),
            )
        )
        return int(result.scalar_one())

    async def _unique_slug(self) -> str:
        for _ in range(20):
            slug = f"demo-{secrets.token_hex(4)}"
            if slug in _RESERVED_SLUGS:
                continue
            exists = await self.db.execute(
                select(School.id).where(School.tenant_slug == slug)
            )
            if exists.scalar_one_or_none() is None:
                return slug
        raise DemoProvisioningError("Could not allocate a unique demo tenant slug")

    async def provision_prospect_session(
        self,
        *,
        display_name: str | None = None,
    ) -> ProspectProvisionResult:
        """Create school + minimal academic shell + principal user (no JWT here)."""
        if not settings.demo_provisioning_allowed:
            raise DemoProvisioningError("Demo provisioning is not enabled")

        active = await self._active_prospect_count()
        if active >= settings.DEMO_MAX_ACTIVE_PROSPECTS:
            raise DemoProvisioningError("Demo capacity reached — try again later")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=settings.DEMO_SESSION_TTL_HOURS)
        raw_session_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_session_token.encode()).hexdigest()
        slug = await self._unique_slug()
        suffix = secrets.token_hex(3).upper()
        school_name = display_name.strip()[:120] if display_name else f"Demo School {suffix}"

        school = School(
            name=school_name,
            code=f"D{suffix}",
            tenant_slug=slug,
            board="SSC",
            contact_email=None,
            is_active=True,
            tenant_kind=TENANT_KIND_PROSPECT_DEMO,
            expires_at=expires_at,
            provisioned_at=now,
            demo_session_token_hash=token_hash,
            settings={
                "ai_budget": {
                    **DEFAULT_AI_BUDGET,
                    "monthly_credits": 50,
                    "teacher_monthly_credits": 15,
                    "incharge_monthly_credits": 30,
                    "limits": {
                        "qp_full_per_month": 3,
                        "qp_regen_per_month": 10,
                    },
                    "plan": "prospect_demo",
                },
                "prospect_demo": True,
            },
        )
        self.db.add(school)
        await self.db.flush()

        ay = AcademicYear(
            school_id=school.id,
            year_label="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 4, 30),
            is_active=True,
        )
        self.db.add(ay)
        await self.db.flush()

        internal_password = secrets.token_urlsafe(24)
        principal = User(
            school_id=school.id,
            username="principal",
            mobile=f"+9199{secrets.randbelow(10**8):08d}",
            full_name="Demo Principal",
            role=UserRole.SUPER_ADMIN,
            password_hash=hash_password(internal_password),
            is_active=True,
        )
        incharge = User(
            school_id=school.id,
            username="incharge",
            mobile=f"+9198{secrets.randbelow(10**8):08d}",
            full_name="Class In-charge",
            role=UserRole.CLASS_INCHARGE,
            password_hash=hash_password(internal_password),
            is_active=True,
        )
        self.db.add(principal)
        self.db.add(incharge)
        await self.db.flush()

        cls = Class(
            school_id=school.id,
            grade="10",
            section="A",
            academic_year_id=ay.id,
            class_incharge_id=incharge.id,
        )
        self.db.add(cls)
        await self.db.flush()

        subject = Subject(
            school_id=school.id,
            name="Mathematics",
            code="MATH10",
            class_id=cls.id,
        )
        self.db.add(subject)
        await self.db.flush()

        self.db.add(
            TeacherSubjectMapping(
                school_id=school.id,
                teacher_id=incharge.id,
                subject_id=subject.id,
                class_id=cls.id,
                is_primary=True,
            )
        )
        await self.db.flush()

        logger.info(
            "prospect_tenant_provisioned",
            school_id=str(school.id),
            tenant_slug=slug,
            expires_at=expires_at.isoformat(),
            onboarding_path=ONBOARDING_PATH,
        )
        return ProspectProvisionResult(
            school=school,
            principal=principal,
            raw_session_token=raw_session_token,
            expires_at=expires_at,
        )
