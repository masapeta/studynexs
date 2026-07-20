# StudyNexs — URL Architecture

> **Canonical URL strategy** for StudyNexs. Deployment mechanics live in
> [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md). Engineering policy:
> [`/CLAUDE.md`](../CLAUDE.md).

**Owner:** Avinash Reddy Masapeta · **Status:** v1.0 draft · **Last updated:** 2026-07-16  
> Freeze after Gate 1A — see [`DEPLOYMENT_CONVENTIONS.md`](./DEPLOYMENT_CONVENTIONS.md) §12.

---

## 1. Purpose

This document defines **what each hostname means**, which hosts are **platform** vs **tenant**,
and how clients route requests to the shared API. It is independent of cloud provider (OCI, Azure,
Cloudflare) and Docker topology.

---

## 2. Hostname map

| Host | Role | Tenant? | Notes |
|------|------|---------|-------|
| `studynexs.com` | Marketing | No | Static marketing site |
| `www.studynexs.com` | Marketing redirect | No | → apex or canonical www |
| `app.studynexs.com` | Production application | Platform | Shared app build; school context via slug or login |
| `api.studynexs.com` | Shared API | Platform | **All** school traffic; tenant via header or JWT |
| `demo.studynexs.com` | Sales / pilot demo | Platform | Demo tenant configured at deploy (`demo` or `test`) |
| `dev.studynexs.com` | Development stack | Platform | Non-production data |
| `test.studynexs.com` | QA / staging | Platform | Pre-release validation |
| `admin.studynexs.com` | Platform operations | Platform | Super-admin / engineering visibility |
| `{school}.studynexs.com` | School tenant | **Yes** | e.g. `dps.studynexs.com`, `abcschool.studynexs.com` |

**Rule:** Only `{school}.studynexs.com` (where `{school}` is not reserved) is a **tenant host**.
All other subdomains are **platform hosts**.

---

## 3. Reserved subdomains

These slugs are **never** school tenants. They must not be assigned as `School.tenant_slug` in
the database.

```
api
app
demo
dev
test
admin
www
```

Registration of a school with a reserved slug should be rejected at provisioning time (future
platform-admin guardrail).

---

## 4. Request flow (target architecture)

```
Browser at dps.studynexs.com
        │
        │  HTTPS
        ▼
Cloudflare Pages (admin-web)
        │
        │  derive tenant slug "dps" from hostname
        │  OR use deploy-time slug on platform hosts (demo, app, …)
        ▼
https://api.studynexs.com/api/v1/...
        │
        │  Host: api.studynexs.com  →  platform host (ignore as tenant)
        │  X-Tenant-Slug: dps
        │  Authorization: Bearer <JWT with school_id>
        ▼
FastAPI validates:
  1. Resolve tenant from header (platform API host)
  2. JWT school_id must match resolved tenant
  3. All queries scoped by school_id
```

---

## 5. Tenant routing rules

### 5.1 API (`api.studynexs.com`)

| Step | Behavior |
|------|----------|
| Host is reserved platform subdomain | **Do not** derive tenant from hostname |
| Tenant source | `X-Tenant-Slug` header (required in production) |
| Authenticated requests | JWT `school_id` must match resolved tenant |
| Unauthenticated auth routes | Same — slug required before user lookup |

Implementation: `app/core/tenant.py` — `TENANT_RESERVED_SUBDOMAINS` + `extract_tenant_slug()`.

### 5.2 School tenant frontend (`{school}.studynexs.com`)

| Step | Behavior |
|------|----------|
| Tenant source | Extract `{school}` from hostname at **runtime** |
| API URL | Always `https://api.studynexs.com` (via `NEXT_PUBLIC_API_URL`) |
| Header sent | `X-Tenant-Slug: {school}` on every API call |

Implementation: `apps/admin-web/src/lib/tenant.ts` — `getTenantSlug()`.

### 5.3 Platform frontend hosts (`demo`, `app`, `dev`, `test`, `admin`)

| Step | Behavior |
|------|----------|
| Tenant source | Deploy-time `NEXT_PUBLIC_TENANT_SLUG` (not hostname) |
| Example | `demo.studynexs.com` → slug `demo` or `test` per seed |

---

## 6. JWT expectations

Access tokens include:

| Claim | Purpose |
|-------|---------|
| `sub` | User ID |
| `school_id` | Tenant scope for all data access |
| `tenant_slug` | Human-readable slug (informational; server validates against DB) |
| `role` | RBAC |
| `jti` | Revocation |
| `sid` | Refresh session (device) |

**Every protected route:** `school_id` from JWT is authoritative for data; request tenant (header
or subdomain) must **match** that `school_id` or the API returns **403**.

Refresh tokens are HttpOnly cookies on the **API origin** (`api.studynexs.com`). Frontends on
other subdomains use `credentials: "include"` with CORS `ALLOWED_ORIGINS` listing each frontend
origin.

---

## 7. API routing rules

| Rule | Detail |
|------|--------|
| Version prefix | All clients use `/api/v1/...` only |
| Shared API | One deployment serves all tenants and all frontends |
| CORS | Explicit HTTPS origins; no `*` in production |
| No tenant in URL path | Tenancy is header/subdomain — not `/api/v1/schools/{id}/...` |
| Health | `/health`, `/ready` — no tenant required |
| Docs | `/docs` disabled in production |

---

## 8. Local development

| Component | Typical URL |
|-----------|-------------|
| Web | `http://localhost:3000` or `http://127.0.0.1:3000` |
| API | `http://127.0.0.1:8000` (Windows: prefer `127.0.0.1` over `localhost`) |
| Tenant | `X-Tenant-Slug: test` or `NEXT_PUBLIC_TENANT_SLUG=test` |
| Base domain | `TENANT_BASE_DOMAIN=localhost` (optional subdomain play: `dps.localhost`) |

Development may fall back to `DEFAULT_TENANT_SLUG` when no header is sent (API only).

---

## 9. Related documents

| Document | Scope |
|----------|-------|
| [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) | Cloud, Docker, env vars, deploy flow |
| [`PLATFORM_ARCHITECTURE.md`](./PLATFORM_ARCHITECTURE.md) | Platform layers, AI/RAG, request flow diagrams |
| [`api/TENANT_AUTH.md`](./api/TENANT_AUTH.md) | Auth + tenant for API clients |
| [`api/CLIENT_INTEGRATION.md`](./api/CLIENT_INTEGRATION.md) | Client integration (v1) |
| [`IP_PROTECTION_GUIDE.md`](./IP_PROTECTION_GUIDE.md) | Domain ownership notes |

---

## 10. Change control

- **URL or reserved-list changes** require updating this file first, then implementation.
- Additive reserved names only (do not remove without deprecation notice).
- Breaking URL changes need `/api/v2` policy per [`api/V1_STABILITY_POLICY.md`](./api/V1_STABILITY_POLICY.md).
