"""Prospect demo tenant lifecycle constants and guards (Stage 2B)."""
from __future__ import annotations

TENANT_KIND_CUSTOMER = "customer"
TENANT_KIND_REFERENCE = "reference"
TENANT_KIND_PILOT = "pilot"
TENANT_KIND_PROSPECT_DEMO = "prospect_demo"

# Only disposable prospect tenants may be purged by cleanup jobs.
PURGEABLE_TENANT_KINDS = frozenset({TENANT_KIND_PROSPECT_DEMO})

ONBOARDING_PATH = "/dashboard/teaching/curriculum/onboarding"
