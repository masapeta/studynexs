"""Regression guard for the audit-logging bug.

AuditMiddleware constructs AuditLog(user_agent=...), but the table had no such
column, so every mutating request's audit insert raised and was silently
swallowed — no audit rows were ever written in production. This test pins the
model to the exact kwargs the middleware uses so the column can't go missing again.
"""
from app.db.models.audit import AuditLog


def test_auditlog_accepts_middleware_kwargs():
    # Mirror exactly what app/core/audit_middleware.py constructs.
    row = AuditLog(
        action="POST /api/v1/example",
        resource_type="example",
        ip_address="127.0.0.1",
        user_agent="pytest-UA",
        details={"status": 201, "duration_ms": 1.2},
    )
    assert row.user_agent == "pytest-UA"
    assert row.resource_type == "example"
