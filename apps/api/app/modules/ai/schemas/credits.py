"""AI credit balance and school usage reports."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreditStatusOut(BaseModel):
    monthly_limit: int
    credits_used: int
    credits_remaining: int
    soft_limit_pct: int = 80
    at_soft_limit: bool = False
    at_hard_limit: bool = False
    user_monthly_limit: int | None = None
    user_credits_used: int = 0
    user_credits_remaining: int | None = None
    override_active: bool = False
    role: str = ""
    purpose_costs: dict[str, int] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)
    usage_counts: dict[str, int] = Field(default_factory=dict)
    billing_policy: str = ""
    # Value metrics (no provider cost)
    papers_this_month: int = 0
    est_hours_saved: float = 0.0


class UsageLogEntry(BaseModel):
    usage_id: uuid.UUID
    generated_at: datetime
    generated_by: str
    class_label: str
    subject: str
    paper_title: str
    purpose_tag: str
    credits_used: int
    approval_status: str
    rejection_reason: str | None = None


class UsageLogOut(BaseModel):
    items: list[UsageLogEntry] = Field(default_factory=list)


class SchoolAIReportOut(BaseModel):
    monthly_limit: int
    credits_used: int
    credits_remaining: int
    at_soft_limit: bool
    at_hard_limit: bool
    override_active: bool
    usage_counts: dict[str, int] = Field(default_factory=dict)
    papers_total: int = 0
    papers_this_month: int = 0
    reports_this_month: int = 0
    est_hours_saved: float = 0.0
    plan: str = "pilot"


class OverrideRequest(BaseModel):
    hours: int = Field(default=24, ge=1, le=72)
