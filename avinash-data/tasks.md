# Academix Platform — Phase 1 Task Tracker

## Phase 1: Backend Foundation — ✅ 100% COMPLETE

### 1.1 Infrastructure
- [x] Repo structure, Docker Compose (`name: academix-platform`), Nginx, Dockerfile
- [x] README.md

### 1.2 Core
- [x] config, database, security, dependencies, tenant

### 1.3 Database Models — 19 models, 23 tables
- [x] All domain models + Notification + UploadedFile
- [x] Alembic migrations (2 revisions applied)

### 1.4 Auth Module — 5 endpoints
- [x] send-otp, verify-otp, login, refresh, logout

### 1.5 Users Module — 6 endpoints
- [x] list (paginated, searchable), me, get, create, update, deactivate

### 1.6 Academic Module — 9 endpoints
- [x] Classes, Subjects, Students, Parent linking, Teacher mapping

### 1.7 Attendance Module — 3 endpoints
- [x] Bulk mark, class attendance, summary

### 1.8 Examinations Module — 4 endpoints
- [x] Create exam, list, bulk marks, get marks

### 1.9 Fees Module — 3 endpoints
- [x] List fees, pay (atomic receipt), download receipt (PDF/HTML)

### 1.10 Timetable Module — 4 endpoints
- [x] Class/teacher view, create slot, delete slot

### 1.11 Communications Module — 3 endpoints
- [x] Create notice, list (role-filtered), mark read

### 1.12 School Ops Module — 7 endpoints
- [x] Library books CRUD, issue/return, events CRUD

### 1.13 Notifications Module — 4 endpoints
- [x] List, unread count, mark read, mark all read

### 1.14 Files Module — 2 endpoints
- [x] Upload (10MB limit), download

### 1.15 Supporting Systems
- [x] Outbox worker (poll, dispatch, retry, dead-letter)
- [x] Outbox helper (emit_event convenience function)
- [x] Audit middleware (auto-log all POST/PUT/PATCH/DELETE)
- [x] Receipt PDF generator (HTML → PDF via weasyprint)

### 1.16 Synthetic Data
- [x] 3 schools, 2,160 students, 3,130 parents, 72 classes, 360 subjects

### 1.17 Integration Tests
- [x] Test framework (conftest, fixtures, auth helpers)
- [x] test_health (2 tests)
- [x] test_auth (3 tests)
- [x] test_users (5 tests)
- [x] test_academic (4 tests)
- [x] test_notifications (3 tests)

---

**Total: 56 API routes | 19 models | 23 tables | 17 test cases**

**BACKEND COMPLETE → Next: `admin-web` frontend portal**
