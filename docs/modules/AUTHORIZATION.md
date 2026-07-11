# Authorization

> Module dashboard · Master: [`../PLATFORM_STATUS.md`](../PLATFORM_STATUS.md)

## Status

**✅ Complete** (continuous hardening)

## Owner

`app/core/authorization.py` · `dependencies.py` · per-route `require_roles`

## Features

| Feature | State |
|---------|-------|
| JWT + refresh rotation | ✅ |
| Tenant isolation (`school_id` from token) | ✅ |
| Role-based route guards | ✅ |
| Staff scope (class incharge, teaching classes) | ✅ |
| Mastery / jobs IDOR fixes | ✅ Batch 1–6 |
| PII masking in logs | ✅ |
| Redis blacklist graceful degrade | ✅ |

## Files

`apps/api/app/core/dependencies.py` · `app/core/authorization.py` · `app/core/tenant_scope.py`

## Tests

`tests/test_authorization.py` · `tests_security/test_sessions.py`

## Prime directive

Never trust client `school_id` — scope every query from `CurrentUser`.
