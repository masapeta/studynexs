# StudyNexs API v1

All public HTTP APIs are under **`/api/v1`**.

| Document | Description |
|----------|-------------|
| [V1_STABILITY_POLICY.md](./V1_STABILITY_POLICY.md) | Breaking vs non-breaking changes |
| [CLIENT_INTEGRATION.md](./CLIENT_INTEGRATION.md) | Mobile / web / external clients |
| [TENANT_AUTH.md](./TENANT_AUTH.md) | School-scoped login and OTP |
| [CHANGELOG.md](./CHANGELOG.md) | API change log |
| [openapi-v1.json](./openapi-v1.json) | OpenAPI 3 schema (regenerate with script below) |

## Regenerate OpenAPI

```bash
cd apps/api
python scripts/export_openapi.py
```

## Modules

| Prefix | Domain |
|--------|--------|
| `/api/v1/auth` | OTP, login, refresh, logout |
| `/api/v1/users` | Users, profile |
| `/api/v1/academic` | Classes, students, subjects |
| `/api/v1/attendance` | Mark & query attendance |
| `/api/v1/fees` | Fees, payments, receipts |
| `/api/v1/files` | Upload / download |
| `/api/v1/notices` | School notices |
| `/api/v1/notifications` | In-app notifications |
| `/api/v1/exams` | Examinations |
| `/api/v1/timetable` | Timetable |
| `/api/v1/ops` | Transport, library, events |
