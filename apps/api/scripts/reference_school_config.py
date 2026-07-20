"""StudyNexs Reference School — single source of truth for showcase tenant constants.

The Reference School (ARM International School) is a permanent product asset:
prospects log in here to experience the full platform end-to-end.
Real customer schools get their own tenant on signup — not this one.
"""

from __future__ import annotations

# Tenant identity
TENANT_SLUG = "reference"
SCHOOL_NAME = "ARM International School"
SCHOOL_CODE = "ARMIS01"
SCHOOL_BOARD = "SSC"

# Demo credentials (shared login card)
DEMO_PASSWORD = "Demo@1234"

# Primary demo personas (seed_demo_ssc + patch_demo_portal_logins)
LOGIN_PRINCIPAL = "principal"
LOGIN_TEACHER_MATHS = "teacher6"  # Class 10 Maths
LOGIN_PARENT = "parent_demo"
LOGIN_STUDENT = "student_demo"
LOGIN_CLASS_INCHARGE = "teacher1"  # Class 10-A incharge (curriculum approvals)

# Legacy slug — do not use for new seeds; kept for migration notes only
LEGACY_TENANT_TEST = "test"
LEGACY_TENANT_NAAGARJUNA = "naagarjuna"
