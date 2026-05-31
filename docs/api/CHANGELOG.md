# API changelog

All notable changes to the public `/api/v1` contract.

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
