# Full product plan and greenfield restart guide

This document merges:

1. **Original product / platform plan** — MVP themes (from `Platform_owner.md`), control-plane vs school-plane scope, and the agreed technical roadmap (B then A).
2. **Greenfield restart plan** — how to start a new codebase (or a disciplined reboot) without repeating earlier process and architecture issues.

---

## Part 1 — Full original plan

### 1.1 Strategy: B first, then A (not “B forever”)

| Phase | Name | Goal |
|-------|------|------|
| **B** | Same backend, real control plane | Platform identity, auth, guards, audit, failed-actions store, recovery APIs — all on **one** API service. |
| **A** | Split operator UI | Dedicated `apps/platform-web` (or `web-platform`) once the spine is real — not before. |

**Hard gates (from original agreement):**

- No impersonation / act-on-behalf until **audit + failed-actions** are trustworthy.
- No long-term dependence on `users.role == super_admin` alone for **platform** APIs; platform operators use **`PlatformUser`** (or equivalent) + explicit permissions.
- **Separate cookie / token namespaces** for school auth vs platform auth when both exist.
- **Module flags** are not UI-only — enforcement belongs in API dependencies (later phase).

### 1.2 Identity model (original intent)

| Actor | Meaning | Scope |
|-------|---------|--------|
| **School user** (`User`, has `school_id`) | Admin, teacher, student, parent, etc. | One school / tenant |
| **`super_admin` (school role)** | Highest privilege **inside that school** — not “owner of the whole product.” | School data plane |
| **Platform operator** (`PlatformUser`) | Onboarding schools, subscriptions, cross-tenant support, audit | Control plane |

**Naming (recommended):**

- **School portal** — day-to-day for one school.
- **Platform console** / **Operator console** — cross-tenant operations.

### 1.3 Technical milestones (original PR-style roadmap)

| Milestone | Content |
|-----------|---------|
| **PR1** | `platform_users` table; lean `role` + `platform_roles` constants; migration; bcrypt aligned with existing security; idempotent `ensure_platform_owner` + CLI bootstrap; tests under `tests/platform/`. |
| **PR2** | Dedicated **platform auth**: `POST /api/v1/platform-auth/login`, `refresh`, `logout`; JWT with `principal_type=platform`; **separate** refresh cookie (e.g. scoped path for platform refresh only); **school JWT rejected** on platform routes; **platform JWT rejected** on school-only routes (e.g. `/auth/me`). |
| **PR3** | `get_current_platform_user`, `require_platform_permission`; migrate **`/api/v1/platform/*`** off school `super_admin` checks; audit and tickets record **platform actor** where applicable. |
| **Later** | Failed-action store; RBAC / permission inspector API; helpdesk depth; act-on-behalf + elevation workflow; impersonation + short-lived tokens + banner; **module matrix** enforced in every module; billing; then **`apps/platform-web`**. |

### 1.4 MVP themes — gap table (original `Platform_owner.md`)

| MVP theme | What exists today | What you still need |
|-----------|-------------------|---------------------|
| **School onboarding** | Static checklist page | APIs + UI: create school, set lifecycle status (draft → active), assign slug, seed first admin, optional CSV pipelines, checklist state in DB |
| **School/tenant management** | Single-school GET/PUT `/schools/me` | List/search schools, suspend/archive, limits, subscription fields, activity — new tables + endpoints |
| **School admin recovery** | Nothing systematic | Password reset/unlock/session revoke endpoints (often privileged), tied to ticket ID + audit |
| **User management across schools** | Per-school user APIs | Cross-school search, move user between schools, duplicate detection — platform queries + constraints |
| **Permission inspector** | Implicit (403 messages) | Explicit evaluator endpoint or shared rule engine that returns allow/deny + reason code (module off, school suspended, missing profile, etc.) |
| **Failed action logs** | App logs / no unified UI | Structured error/event store (request id, school_id, user_id, route, code); expose platform list/filter API |
| **Helpdesk tickets** | Nothing (or MVP stub) | Ticket store, SLA fields, assignments, links to school/user — module (MVP can be basic CRUD) |
| **Act-on-behalf + audit** | No safe wrapper | Elevation workflow: reason/ticket, preview, execute via service role or audited impersonation; append-only audit with before/after |
| **Impersonation + audit** | Nothing | Short-lived tokens, banner in UI, scoped claims, full audit stream |
| **Module/feature control** | School settings JSON exists partially | Explicit module flags per school + enforcement in every module’s dependencies |

### 1.5 Staff / web split (original end state)

- **`staff-web` (or `web-school`)** — school JWT, tenant headers, school roles.
- **`platform-web`** — platform JWT only; no mixed “second login in same app” long term; bridge acceptable only as a temporary migration path.

---

## Part 2 — Greenfield restart plan (avoid previous issues)

Use this when starting a **new repo** or a **disciplined v2** so you do not repeat: no git history, Alembic run from wrong directory, broken `down_revision` chains, ambiguous “super admin,” and half-finished refactors that leave dead imports.

### 2.1 What “from scratch” means (choose one)

| Option | Best when |
|--------|------------|
| **A. Greenfield repo** | You can discard old code; you want clean history and layout. |
| **B. New repo + selective copy** | Old app has tests/schemas worth copying file-by-file. |
| **C. Same repo, “v2” folder** | Rare; prefer A or B. |

**Non-negotiable:** **`git init` day one**, remote, small commits, **tags** at milestones (`v0.1-auth`, `v0.2-tenancy`, …).

### 2.2 Repository layout (monorepo, one obvious Alembic home)

```text
school-platform/
  README.md                 # Bold: all DB commands from apps/api
  .gitignore
  .env.example
  docker-compose.yml        # optional: postgres + redis
  apps/
    api/
      alembic.ini           # ONLY HERE for API database
      alembic/
      app/
      tests/
    web-school/
    web-platform/           # later; separate deploy
  docs/
    ADR/                    # Architecture Decision Records
    RUNBOOK.md              # migrations, deploy, rollback
```

**Rule:** Any Postgres migration for the product runs as:

```bash
cd apps/api && alembic upgrade head
```

Never assume `alembic.ini` exists at repo root unless you add an optional wrapper that points `-c apps/api/alembic.ini`.

### 2.3 Identity and auth (from day one, documented)

- **ADR #1** (one page): school JWT vs platform JWT; cookie namespaces; which routes accept which principal.
- Implement **platform auth** when the **first** cross-tenant write/read API appears — not as a retrofit six months later.

### 2.4 Database and Alembic

1. **Linear chain:** every revision’s `down_revision` must point to a file that **exists** in the repo.
2. After adding a migration: `alembic upgrade head` locally; optionally `downgrade -1` to verify.
3. **CI:** ephemeral Postgres — `alembic upgrade head` (and downgrade for new revisions when safe).

### 2.5 API boundaries

- Prefix: `/api/v1/...`.
- Modules: `school_*` (tenant-scoped) vs `platform_*` (control plane).
- Dependencies: `get_current_school_user` + tenant check vs `get_current_platform_user` + permission map.

### 2.6 Testing minimum (week one onward)

- Smoke: app imports, `/health`.
- Auth: login → me → 401 without token.
- RBAC: one allow + one deny per sensitive area.
- Migration smoke in CI on empty DB.

### 2.7 Delivery phases (order that limits rework)

1. Repo + Docker Postgres/Redis + Alembic + health + **git** + **CI skeleton**.
2. School + `User` + school JWT + tenant resolution.
3. One **vertical slice** (e.g. admin user list) end-to-end.
4. `platform_users` + platform JWT + first `/platform` API.
5. **`web-platform`** app (separate).
6. Billing / subscriptions (platform-scoped) when the model is fixed.
7. School feature modules in slices + module flags + API enforcement.

End each phase with: **tag**, migrations applied, tests green, README updated.

### 2.8 Operations

- Backups before production migrations.
- **RUNBOOK:** `upgrade`, `downgrade -1`, when to use `alembic stamp` (rare, DBA-approved only).

### 2.9 Anti-regression checklist

| Past issue | Prevention |
|------------|------------|
| Alembic “no config file” from repo root | Document `cd apps/api`; README one-liner with `alembic -c apps/api/alembic.ini` from root if desired |
| Broken migration parent | CI + review `down_revision` |
| Cannot revert | Git + small commits + tags |
| Platform vs school confusion | ADR #1 + naming + separate apps/JWTs |
| Dead imports | CI import / test gate on PR |
| Awkward dual login UX | Separate `web-platform` when operators are first-class |

### 2.10 What to salvage from an old repo (if option B)

Copy: tests that encode business rules, stable domain logic, fee/attendance pieces that were production-verified.

Do **not** copy: broken Alembic links, ambiguous RBAC, or “platform” behavior implemented only as school `super_admin` without documentation.

---

## Part 3 — How this doc relates to `Platform_owner.md`

- **`Platform_owner.md`** remains the short **MVP gap table** at repo root (or you may replace it with a link to this file).
- **`docs/FULL_PRODUCT_PLAN_AND_GREENFIELD_RESTART.md`** (this file) is the **single long-form** reference: original product/technical plan **plus** greenfield process.

---

*Generated for the Academix / school-management-system product line. Update ADRs and tables as decisions change.*
