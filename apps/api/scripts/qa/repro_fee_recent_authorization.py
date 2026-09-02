"""Reproduce and verify school-wide fee aggregate authorization."""
from __future__ import annotations

from qa_common import call, env, login

tenant = env("QA_TENANT", "reference")
admin = login(tenant, env("QA_ADMIN_USERNAME", "admin1"), env("QA_ADMIN_PASSWORD"))
teacher = login(tenant, env("QA_TEACHER_USERNAME", "teacher6"), env("QA_TEACHER_PASSWORD"))

for label, token, expected in (("admin", admin, 200), ("teacher", teacher, 403)):
    response = call("GET", "/api/v1/fees/recent?limit=50", tenant=tenant, token=token)
    ok = response.status == expected
    print(f"{label}: HTTP {response.status} (expected {expected}) -> {'PASS' if ok else 'FAIL'}")
    if label == "teacher" and response.status == 200:
        print("  SECURITY FAILURE: teacher can enumerate school-wide payment history")
    if not ok:
        raise SystemExit(1)
