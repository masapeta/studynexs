# API changelog

All notable changes to the public `/api/v1` contract.

## [Unreleased]

### Added

- `GET /portal/timetable` — the signed-in student's class timetable
- `GET /portal/child/{studentId}/timetable` — a linked child's class timetable
- `GET /portal/report-cards` and `GET /portal/report-cards/{reportId}` — the signed-in
  student's report cards
- `GET /portal/child/{studentId}/report-cards` and
  `GET /portal/child/{studentId}/report-cards/{reportId}` — a linked child's report cards
- `not_assessed` (list of subject names) on report-card responses, including the staff
  `/ai/report-cards*` endpoints (additive)

### Security

- `/portal/timetable` and `/portal/report-cards*` are student-only (own record);
  `/portal/child/{studentId}/*` is parent-only and limited to linked children (`403` otherwise)
- Learner report cards list only approved cards whose every included exam has published
  results; figures reflect the published results, the remark is withheld (`remark_withheld`)
  when they differ from the approved card, and an unavailable card returns `404`

## [1.1.0] - 2026-05-22

### Added

- Per-endpoint Redis rate limits on hot paths
- Metrics middleware (`http_request` logs, `X-Response-Time-Ms` header)
- Tenant validation on authenticated requests (subdomain / `X-Tenant-Slug`)
- Object-level authorization for fees, files, student parents
- Embedded outbox worker when `OUTBOX_WORKER_ENABLED=true`
- Audit log retention job (`scripts/purge_audit_logs.py`)

### Security

- File download scoped to `school_id`
- Fee payment restricted to admin/parent (linked student)

## [1.0.0] - Initial

- `/api/v1` modular monolith surface (auth, users, academic, attendance, fees, …)
