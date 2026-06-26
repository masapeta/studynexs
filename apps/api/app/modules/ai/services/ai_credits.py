"""AI credit metering — permissioned, budgeted, school-value oriented.

Credits are charged at **generation time** (when the LLM runs), not at approval.
Rejected or abandoned drafts still consume credits — the provider cost is already incurred.

Every LLM-backed action is checked before execution and recorded after with credits_charged.
Schools see credits and time saved — never provider cost (operator-only).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings
from app.core.database import async_session_factory
from app.db.models.ai_usage import AIUsage
from app.db.models.school import School

settings = get_settings()

# Credits per action (purpose_tag). Charged when the LLM call completes.
# Clone/duplicate uses no LLM — zero credits (see duplicate_question_paper endpoint).
CREDIT_RULES: dict[str, int] = {
    "qp_full": 5,              # Fresh generate — full LLM paper
    "qp_from_bank": 2,         # Compose from school question bank + small LLM fill
    "qp_clone": 0,             # Clone & modify — no LLM (reserved; duplicate endpoint today)
    "qp_regen_full": 4,
    "qp_regen_section": 2,
    "qp_regen_question": 1,
    "worksheet": 2,
    "marking_scheme": 2,
    "quality_check": 1,
    "report_card": 3,
    "mastery_narrative": 1,
    "exam_evaluation": 2,
}

BILLING_POLICY = (
    "AI credits are charged when content is generated, not when it is approved or rejected. "
    "Generated drafts consume credits even if not approved."
)

FEATURE_DEFAULT_PURPOSE: dict[str, str] = {
    "question_paper": "qp_full",
    "report_card": "report_card",
    "mastery_flag": "mastery_narrative",
}

# Pilot defaults — 1 school can run safely without cost explosion.
DEFAULT_AI_BUDGET: dict[str, Any] = {
    "monthly_credits": 100,
    "soft_limit_pct": 80,
    "teacher_monthly_credits": 25,
    "incharge_monthly_credits": 60,
    "limits": {
        "qp_full_per_month": 5,
        "qp_regen_per_month": 20,
    },
    "plan": "pilot",
    "override_until": None,
}

DEFAULT_SCHOOL_TIMEZONE = "Asia/Kolkata"

_ADMIN_ROLES = frozenset({"admin", "super_admin"})
_INCHARGE_ROLES = frozenset({"class_incharge"})


def school_timezone(school: School | None) -> ZoneInfo:
    tz_name = DEFAULT_SCHOOL_TIMEZONE
    if school and school.settings:
        tz_name = school.settings.get("timezone") or DEFAULT_SCHOOL_TIMEZONE
    try:
        return ZoneInfo(str(tz_name))
    except Exception:
        return ZoneInfo(DEFAULT_SCHOOL_TIMEZONE)


def month_start_for_school(school: School | None = None) -> datetime:
    """First instant of the billing month in the school's timezone, as UTC."""
    tz = school_timezone(school)
    now_local = datetime.now(tz)
    start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_local.astimezone(timezone.utc)


def month_start() -> datetime:
    """UTC month boundary — prefer month_start_for_school when a School is available."""
    return month_start_for_school(None)


def credits_for_purpose(purpose_tag: str) -> int:
    return CREDIT_RULES.get(purpose_tag, 1)


def get_school_ai_budget(school: School) -> dict[str, Any]:
    raw = (school.settings or {}).get("ai_budget") or {}
    budget = {**DEFAULT_AI_BUDGET, **raw}
    budget["limits"] = {**DEFAULT_AI_BUDGET["limits"], **(raw.get("limits") or {})}
    return budget


def override_active(budget: dict[str, Any]) -> bool:
    until = budget.get("override_until")
    if not until:
        return False
    try:
        ts = datetime.fromisoformat(str(until).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < ts
    except (TypeError, ValueError):
        return False


async def _sum_credits(
    db: AsyncSession,
    school_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    purpose_tag: str | None = None,
    since: datetime | None = None,
) -> int:
    q = select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
        AIUsage.school_id == school_id
    )
    if user_id:
        q = q.where(AIUsage.created_by == user_id)
    if purpose_tag:
        q = q.where(AIUsage.purpose_tag == purpose_tag)
    if since:
        q = q.where(AIUsage.created_at >= since)
    return int((await db.execute(q)).scalar_one() or 0)


async def _count_purpose(
    db: AsyncSession,
    school_id: uuid.UUID,
    purpose_tag: str,
    *,
    user_id: uuid.UUID | None = None,
    since: datetime | None = None,
) -> int:
    q = select(func.count()).select_from(AIUsage).where(
        AIUsage.school_id == school_id,
        AIUsage.purpose_tag == purpose_tag,
    )
    if user_id:
        q = q.where(AIUsage.created_by == user_id)
    if since:
        q = q.where(AIUsage.created_at >= since)
    return int((await db.execute(q)).scalar_one() or 0)


async def _lock_school_row(db: AsyncSession, school_id: uuid.UUID) -> School:
    """Row lock — serializes credit checks/charges for one school within a transaction."""
    result = await db.execute(
        select(School).where(School.id == school_id).with_for_update()
    )
    return result.scalar_one()


@dataclass
class UsageSnapshot:
    budget: dict[str, Any]
    since: datetime
    monthly_limit: int
    school_used: int
    user_limit: int | None
    user_used: int
    usage_counts: dict[str, int]

    @property
    def credits_remaining(self) -> int:
        return max(0, self.monthly_limit - self.school_used)

    @property
    def user_credits_remaining(self) -> int | None:
        if self.user_limit is None:
            return None
        return max(0, self.user_limit - self.user_used)

    @property
    def at_hard_limit(self) -> bool:
        return self.school_used >= self.monthly_limit and not override_active(self.budget)

    @property
    def at_soft_limit(self) -> bool:
        soft_pct = int(self.budget.get("soft_limit_pct") or 80)
        pct = (self.school_used / self.monthly_limit * 100) if self.monthly_limit else 100
        return pct >= soft_pct and not override_active(self.budget)


async def _build_usage_snapshot(
    db: AsyncSession,
    school: School,
    *,
    user_id: uuid.UUID,
    role: str,
) -> UsageSnapshot:
    budget = get_school_ai_budget(school)
    since = month_start_for_school(school)
    monthly_limit = int(budget["monthly_credits"])
    school_used = await _sum_credits(db, school.id, since=since)

    user_limit: int | None = None
    if role in _ADMIN_ROLES:
        user_limit = None
    elif role in _INCHARGE_ROLES:
        user_limit = int(budget.get("incharge_monthly_credits") or 60)
    elif role == "teacher":
        user_limit = int(budget.get("teacher_monthly_credits") or 25)

    user_used = await _sum_credits(db, school.id, user_id=user_id, since=since)
    limits_cfg = budget.get("limits") or {}
    usage_counts = {
        "qp_full": await _count_purpose(db, school.id, "qp_full", since=since),
        "qp_regen_full": await _count_purpose(db, school.id, "qp_regen_full", since=since),
        "qp_regen_section": await _count_purpose(db, school.id, "qp_regen_section", since=since),
        "qp_regen_question": await _count_purpose(db, school.id, "qp_regen_question", since=since),
    }
    return UsageSnapshot(
        budget=budget,
        since=since,
        monthly_limit=monthly_limit,
        school_used=school_used,
        user_limit=user_limit,
        user_used=user_used,
        usage_counts=usage_counts,
    )


def _validate_credit_charge(
    snap: UsageSnapshot,
    *,
    role: str,
    purpose_tag: str,
    cost: int,
) -> None:
    if override_active(snap.budget):
        return

    if snap.at_hard_limit or snap.credits_remaining < cost:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "School AI credit limit reached for this month. "
                "Contact your principal for an emergency override."
            )
            if snap.at_hard_limit
            else f"Not enough school AI credits ({snap.credits_remaining} left, need {cost}).",
        )

    if role in ("teacher", "class_incharge"):
        if snap.user_credits_remaining is not None and snap.user_credits_remaining < cost:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Your monthly AI quota is exhausted ({snap.user_limit} credits). "
                    "Ask your class incharge or principal to review drafts."
                ),
            )
        limits = snap.budget.get("limits") or {}
        if purpose_tag == "qp_full":
            cap = int(limits.get("qp_full_per_month") or 5)
            if snap.usage_counts.get("qp_full", 0) >= cap:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"School pilot limit: max {cap} full question papers per month.",
                )
        if purpose_tag.startswith("qp_regen"):
            cap = int(limits.get("qp_regen_per_month") or 20)
            regen_used = (
                snap.usage_counts.get("qp_regen_full", 0)
                + snap.usage_counts.get("qp_regen_section", 0)
                + snap.usage_counts.get("qp_regen_question", 0)
            )
            if regen_used >= cap:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"School pilot limit: max {cap} paper regenerations per month.",
                )


@dataclass
class CreditStatus:
    monthly_limit: int
    credits_used: int
    credits_remaining: int
    soft_limit_pct: int
    at_soft_limit: bool
    at_hard_limit: bool
    user_monthly_limit: int | None
    user_credits_used: int
    user_credits_remaining: int | None
    override_active: bool
    role: str
    purpose_costs: dict[str, int]
    limits: dict[str, int]
    usage_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "monthly_limit": self.monthly_limit,
            "credits_used": self.credits_used,
            "credits_remaining": self.credits_remaining,
            "soft_limit_pct": self.soft_limit_pct,
            "at_soft_limit": self.at_soft_limit,
            "at_hard_limit": self.at_hard_limit,
            "user_monthly_limit": self.user_monthly_limit,
            "user_credits_used": self.user_credits_used,
            "user_credits_remaining": self.user_credits_remaining,
            "override_active": self.override_active,
            "role": self.role,
            "purpose_costs": self.purpose_costs,
            "limits": self.limits,
            "usage_counts": self.usage_counts,
            "billing_policy": BILLING_POLICY,
        }


async def get_credit_status(
    db: AsyncSession,
    school: School,
    *,
    user_id: uuid.UUID,
    role: str,
) -> CreditStatus:
    snap = await _build_usage_snapshot(db, school, user_id=user_id, role=role)
    soft_pct = int(snap.budget.get("soft_limit_pct") or 80)
    limits_cfg = snap.budget.get("limits") or {}
    return CreditStatus(
        monthly_limit=snap.monthly_limit,
        credits_used=snap.school_used,
        credits_remaining=snap.credits_remaining,
        soft_limit_pct=soft_pct,
        at_soft_limit=snap.at_soft_limit,
        at_hard_limit=snap.at_hard_limit,
        user_monthly_limit=snap.user_limit,
        user_credits_used=snap.user_used,
        user_credits_remaining=snap.user_credits_remaining,
        override_active=override_active(snap.budget),
        role=role,
        purpose_costs=dict(CREDIT_RULES),
        limits={k: int(v) for k, v in limits_cfg.items()},
        usage_counts=snap.usage_counts,
    )


async def check_ai_credits(
    db: AsyncSession,
    school: School,
    *,
    user_id: uuid.UUID,
    role: str,
    purpose_tag: str,
) -> int:
    """Pre-flight credit check (row-locked). Returns credits that will be charged."""
    cost = credits_for_purpose(purpose_tag)

    async def _run_check(session: AsyncSession) -> None:
        locked = await _lock_school_row(session, school.id)
        snap = await _build_usage_snapshot(session, locked, user_id=user_id, role=role)
        _validate_credit_charge(snap, role=role, purpose_tag=purpose_tag, cost=cost)

    if settings.ENVIRONMENT == Environment.TESTING:
        await _run_check(db)
        return cost

    async with async_session_factory() as meter_session:
        try:
            await _run_check(meter_session)
            await meter_session.commit()
        except Exception:
            await meter_session.rollback()
            raise
    return cost


async def assert_credits_for_charge(
    db: AsyncSession,
    school_id: uuid.UUID,
    *,
    user_id: uuid.UUID,
    role: str,
    purpose_tag: str,
    credits: int,
) -> None:
    """Hard enforcement at INSERT time — prevents concurrent overspend past school cap."""
    locked = await _lock_school_row(db, school_id)
    snap = await _build_usage_snapshot(db, locked, user_id=user_id, role=role)
    _validate_credit_charge(snap, role=role, purpose_tag=purpose_tag, cost=credits)


async def reserve_ai_credits(
    db: AsyncSession,
    school_id: uuid.UUID,
    *,
    user_id: uuid.UUID,
    role: str,
    purpose_tag: str,
    feature: str,
    credits: int | None = None,
    ref_type: str | None = None,
) -> AIUsage:
    """Reserve credits before an LLM call — lock, validate, insert placeholder usage row.

    The row is finalized after the provider returns (see finalize_llm_usage). This prevents
    spending provider cost when caps are already exhausted and closes the concurrent
    overspend race without re-checking caps after the LLM has run.
    """
    cost = credits if credits is not None else credits_for_purpose(purpose_tag)
    locked = await _lock_school_row(db, school_id)
    snap = await _build_usage_snapshot(db, locked, user_id=user_id, role=role)
    _validate_credit_charge(snap, role=role, purpose_tag=purpose_tag, cost=cost)
    row = AIUsage(
        school_id=school_id,
        created_by=user_id,
        feature=feature,
        provider="reserved",
        model="reserved",
        purpose_tag=purpose_tag,
        credits_charged=cost,
        role=role,
        ref_type=ref_type,
    )
    db.add(row)
    await db.flush()
    return row


async def set_principal_override(
    db: AsyncSession,
    school: School,
    *,
    hours: int = 24,
) -> dict[str, Any]:
    settings = dict(school.settings or {})
    budget = get_school_ai_budget(school)
    until = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
        hours=max(1, min(hours, 72))
    )
    budget["override_until"] = until.isoformat()
    settings["ai_budget"] = budget
    school.settings = settings
    await db.flush()
    return budget
