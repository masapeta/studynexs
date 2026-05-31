MVP theme	What exists today	What you still need
School onboarding
Static checklist page
APIs + UI: create school, set lifecycle status (draft → active), assign slug, seed first admin, optional CSV pipelines, checklist state in DB
School/tenant management
Single-school GET/PUT /schools/me
List/search schools, suspend/archive, limits, subscription fields, activity—new tables + endpoints
School admin recovery
Nothing systematic
Password reset/unlock/session revoke endpoints (often privileged), tied to ticket ID + audit
User management across schools
Per-school user APIs
Cross-school search, move user between schools, duplicate detection—platform queries + constraints
Permission inspector
Implicit (403 messages)
Explicit evaluator endpoint or shared rule engine that returns allow/deny + reason code (module off, school suspended, missing profile, etc.)
Failed action logs
App logs / no unified UI
Structured error/event store (request id, school_id, user_id, route, code); expose platform list/filter API
Helpdesk tickets
Nothing
Ticket store, SLA fields, assignments, links to school/user—new module (even if MVP is basic CRUD)
Act-on-behalf + audit
No safe wrapper
Elevation workflow: reason/ticket, preview, execute via service role or audited impersonation; append-only audit with before/after
Impersonation + audit
Nothing
Short-lived tokens, banner in UI, scoped claims, full audit stream
Module/feature control
School settings JSON exists partially
Explicit module flags per school + enforcement in every module’s dependencies