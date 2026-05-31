# Client integration guide (v1)

## Base URL

| Environment | Example |
|-------------|---------|
| Local API | `http://localhost:8000` |
| Local via Nginx | `http://localhost` |
| Production | `https://{tenant}.studynexs.com` |

Set admin web: `NEXT_PUBLIC_API_URL`.

## Authentication

1. `POST /api/v1/auth/login` or OTP verify → JSON includes **`access_token`** (top level, not wrapped in `data`).
2. Store access token **in memory** (not `localStorage`).
3. Refresh: `POST /api/v1/auth/refresh` with **credentials** (HttpOnly cookie).
4. Send `Authorization: Bearer <access_token>` on protected routes.
5. On `401`, refresh once then retry; on failure redirect to login.

## Tenant header (dev / API clients)

```
X-Tenant-Slug: your-school-slug
```

Required in production when not using subdomain routing.

## Pagination

List endpoints use `page`, `page_size` (max 100). Response: `items`, `total`, `total_pages`.

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Validation / business rule |
| 401 | Missing or invalid token |
| 403 | Role or tenant mismatch |
| 404 | Resource not found |
| 429 | Rate limited — honor `Retry-After` |

## Rate limits

Authenticated limits are per **user + school**, not only IP. Expect `429` under abuse; back off using `Retry-After`.

## Versioning

Always call `/api/v1/...`. Do not use unversioned paths. Future breaking changes will use `/api/v2`.
