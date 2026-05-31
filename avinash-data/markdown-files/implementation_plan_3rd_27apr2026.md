# Attendance Service Implementation Plan

This plan outlines the architecture and implementation steps for the new `attendance-service`. This service will handle student daily attendance and enforce strict RBAC, fully utilizing the newly built `StaffDesignation` system (Substitute Teachers) and `Class Incharge` assignments.

## User Review Required

> [!IMPORTANT]  
> **Microservice Setup vs Monolith**  
> We will create `attendance-service` as a brand new, standalone microservice running on port `8003`. It will follow the exact same architectural pattern as `academic-service` (sharing the DB and Redis for auth), maintaining our strict microservice boundary.

## Open Questions

> [!NOTE]  
> **1. Daily vs Subject-Wise Attendance?**  
> The plan assumes **Daily Attendance** (marked once a day by the Class Teacher or their active Substitute). Do you also need Subject-Wise attendance (marked by every subject teacher per period) right now, or should we stick to daily for Phase 1?
> 
> **2. Default Status?**  
> If a teacher doesn't explicitly mark a student, should the system assume they are `PRESENT`, or should it remain `UNMARKED` (Null) until the teacher actively submits the register? (The plan currently assumes explicit submission is required, defaulting to `UNMARKED`).

## Proposed Changes

---

### Database Models (`auth-service/app/models`)

The database models remain the single source of truth inside `auth-service`.

#### [MODIFY] [academic.py](file:///c:/Users/avina/Documents/Projects/school-management-system/services/auth-service/app/models/academic.py)
- Create `AttendanceStatus` Enum (`PRESENT`, `ABSENT`, `LATE`, `HALF_DAY`, `EXCUSED`).
- Create `AttendanceRecord` model:
  - `id` (UUID)
  - `school_id` (UUID, FK)
  - `class_id` (UUID, FK)
  - `student_id` (UUID, FK)
  - `date` (Date)
  - `status` (Enum)
  - `remarks` (String, nullable)
  - `marked_by_id` (UUID, FK to users - tracks exactly who marked it)
  - Unique Constraint: `(school_id, class_id, student_id, date)` to prevent duplicates.

#### [NEW] Database Migration
- Generate and apply Alembic migration for the `attendance_records` table.

---

### Attendance Service (`services/attendance-service`)

We will scaffold a new microservice from scratch.

#### [NEW] Dockerfile & .env
- Create a `Dockerfile` identical to `academic-service`.
- Create `.env` mapped to `APP_NAME=SMS Attendance Service`.

#### [NEW] [main.py](file:///c:/Users/avina/Documents/Projects/school-management-system/services/attendance-service/app/main.py)
- Standard FastAPI setup with Redis, Postgres, and Exception handlers.

#### [NEW] API Endpoints & Schemas
- `POST /api/v1/attendance/daily`
  - Body: `class_id`, `date`, `records` (list of `student_id` and `status`).
  - Logic: Inserts or Updates (upserts) the daily attendance for the class.
- `GET /api/v1/attendance/daily`
  - Query: `class_id`, `date`.
  - Logic: Returns the attendance register for the class on that date.
- `GET /api/v1/attendance/student/{student_id}`
  - Query: `start_date`, `end_date`.
  - Logic: Returns a specific student's attendance history.

#### [NEW] Business Logic & RBAC (`app/services/attendance.py`)
- **Strict Authorization Check:** Before a teacher can mark attendance for a `class_id` on a specific `date`, the service will verify:
  1. Is the `current_user` an **Admin/Super Admin**? (Allowed).
  2. Is the `current_user` the **Class Incharge** for `class_id`? (Allowed).
  3. Does the `current_user` have an active **StaffDesignation** as `substitute_teacher` for `class_id` covering `date`? (Allowed).
  - If none apply -> `403 Forbidden`.

---

### Infrastructure (`infra/docker`)

#### [MODIFY] [docker-compose.dev.yml](file:///c:/Users/avina/Documents/Projects/school-management-system/infra/docker/docker-compose.dev.yml)
- Add the `attendance-service` block.
- Map internal port `8000` to external port `8003`.
- Mount volumes for hot-reloading.

## Verification Plan

### Automated Tests
- N/A for this phase, sticking to manual end-to-end verification.

### Manual Verification
1. `docker compose up -d` to build and start the new `attendance-service` on `:8003`.
2. Apply DB migrations via `auth-service`.
3. Use Swagger at `http://localhost:8003/docs`.
4. Log in as **Teacher A** (Class Incharge) and successfully mark daily attendance.
5. Log in as **Teacher B** (Random Teacher) and attempt to mark attendance for Teacher A's class -> **Expect 403 Forbidden**.
6. Log in as **Admin**, assign Teacher B as a `substitute_teacher` for today.
7. Log in as **Teacher B** again and successfully mark attendance for Teacher A's class.
