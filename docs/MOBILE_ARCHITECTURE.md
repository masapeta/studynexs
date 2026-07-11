# Mobile Architecture (Flutter)

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) Part XIV (§98–§105, canonical). **Status:
> 0% built** — no `mobile/` apps exist yet. This doc captures the standard + the API-readiness gaps so
> the foundation is built correctly when its turn comes (after the shared API/RBAC/design contracts
> stabilize).

## Standard

- **Flutter (latest stable) / Dart** is the framework for Android + iOS (+ tablets, future desktop).
- Apps mirror the portals: **Teacher · Parent · Student** mobile (+ future Super-Admin). Super-Admin is web-first; **no separate AI Tutor app** — AI is embedded per role.
- **Business logic lives once, in the backend.** Clients render + orchestrate; they never own domain rules, money math, grading, or authorization. Every client consumes the **same `/api/v1`** (same `APIResponse` envelope, same auth, same tenant model).
- **Architecture:** feature-first + clean architecture; Riverpod (state); GoRouter (nav, deep links); Dio (networking, mirrors the web `api()` client — `X-Tenant-Slug` + Bearer + refresh + typed errors); Freezed + json_serializable (models mirror backend schemas); Flutter Secure Storage (tokens); Firebase Messaging + local notifications (push).
- **Shared, not re-implemented:** auth, RBAC/permissions (`GET /users/me/permissions`), feature flags, notifications, AI services, design tokens.

## Target monorepo shape (introduce at mobile phase — §101)

```
mobile/{teacher,parent,student}/        # Flutter apps
packages/{api-client,design-system,shared-models,shared-utils,ai-sdk}/   # shared, no forked logic
```
Today: only `apps/{api,admin-web}` exist; `packages/` = 0. Keep backend + web seams clean now so
extraction into `packages/` is cheap later.

## API-readiness gaps to close before/with mobile (from the Phase-1 assessment)

| Gap | Why it blocks mobile | Fix |
|---|---|---|
| **Refresh is browser-only** (HttpOnly cookie, path-scoped) | Native clients have no cookie-jar/path semantics | Add a native-client grant: return a rotating refresh token in the body for non-cookie clients |
| **No push infrastructure** | FCM dispatch is a `pass` stub; no device-registration endpoint | Build device registration + server-driven FCM (tenant/role-scoped, minimal payload) |
| **No offline-sync primitives** | `updated_at` absent from domain schemas; offset-only paging | Add `updated_at` + cursor paging; queued idempotent mutations (attendance's ON-CONFLICT upsert is already the right shape) |
| **PWA not phone-usable** | pinch-zoom disabled; no mobile nav <768px | Fix in web first (→ [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md)) |

## Offline-first (§104) & push (§105)

- Local cache for reads; queued mutations for writes; sync is idempotent + conflict-aware; server
  remains the authority (re-validates on sync); cache only the authenticated user's school data,
  encrypted at rest, wiped on logout.
- Push is server-driven + tenant-scoped; least data in payload (no marks/fees/messages); deep-link via
  GoRouter respecting auth/RBAC on arrival; FCM tokens scoped to user+school, revoked on logout.

## Parity rule (§102, §103)
Web and mobile expose the **same capabilities** (presentation may differ). AI behavior never differs
by platform — every client calls the same gateway-backed AI endpoints; grounding/metering/HITL are
enforced server-side, so clients inherit them for free.
