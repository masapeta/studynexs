"""Role-restricted assistant domains — explains "not available for your role" honestly.

Used only AFTER planning, when a turn would otherwise end in the generic guide card. It never
selects tools, never grants access and never changes the planner backend; it only replaces an
unhelpful guide with an explicit, non-leaky denial when the request is clearly about a domain the
caller's role cannot use. Authorization stays in the capabilities themselves.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RestrictedDomain:
    key: str
    label: str
    pattern: re.Pattern[str]
    allowed_roles: frozenset[str]


_FEES = re.compile(
    r"\b(fees?|dues|outstanding (amount|fees?)|fee collection|collected|payments?|receipts?)\b",
    re.I,
)
_STAFF_DIRECTORY = re.compile(r"\b(payroll|salar(y|ies)|staff (list|directory))\b", re.I)

RESTRICTED_DOMAINS: tuple[RestrictedDomain, ...] = (
    RestrictedDomain(
        "fees",
        "Fees",
        _FEES,
        # Parents see their own children's fees through their own capability.
        frozenset({"admin", "super_admin", "parent"}),
    ),
    RestrictedDomain(
        "payroll",
        "Payroll and staff records",
        _STAFF_DIRECTORY,
        frozenset({"admin", "super_admin"}),
    ),
)

_ROLE_LABELS = {
    "super_admin": "Principal",
    "admin": "Admin",
    "class_incharge": "Class Incharge",
    "teacher": "Subject Teacher",
    "operations": "Operations",
    "parent": "Parent",
    "student": "Student",
}


def restricted_domain_for(text: str, role: str) -> RestrictedDomain | None:
    """The first restricted domain the request is about that this role may not use."""
    for domain in RESTRICTED_DOMAINS:
        if role not in domain.allowed_roles and domain.pattern.search(text or ""):
            return domain
    return None


def role_denied_block(domain: RestrictedDomain, role: str) -> dict[str, Any]:
    role_label = _ROLE_LABELS.get(role, role.replace("_", " ").title())
    return {
        "kind": "not_found",
        "title": f"{domain.label} isn't available for your role",
        "message": (
            f"Your role ({role_label}) doesn't have access to {domain.label.lower()}. "
            "If you need this, ask your school administrator."
        ),
    }
