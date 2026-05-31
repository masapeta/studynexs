# Tenant-scoped authentication

## How login resolves a school

Unauthenticated routes (`/api/v1/auth/login`, `/send-otp`, `/verify-otp`) resolve the school **before** looking up users:

1. **Subdomain** — `sia.studynexs.com` → tenant slug `sia`
2. **Header** — `X-Tenant-Slug: test` (local dev and tests)
3. **Dev default** — `DEFAULT_TENANT_SLUG` when `ENVIRONMENT=development` and no header

Username and mobile are unique **per school** (`uq_users_school_mobile`, `uq_users_school_username`), not globally. The same mobile can exist at two schools; OTP and login only match users in the resolved school.

## Client requirements

| Client | Requirement |
|--------|-------------|
| Admin web (local) | Send `X-Tenant-Slug` or use subdomain matching seeded school |
| Mobile / API | Always send `X-Tenant-Slug` or use school subdomain |
| Tests | `X-Tenant-Slug: test` on the HTTP client (see `conftest.py`) |

After login, `validate_tenant_school_match` ensures the JWT `school_id` matches the request tenant.

## Migration

Apply school-scoped identity constraints:

```bash
cd apps/api
alembic upgrade head
```

Revision: `b2c3d4e5f6a7_user_school_scoped_identity`.
