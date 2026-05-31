# Attendance Service Walkthrough

The `attendance-service` is now fully operational and running locally on port `8003`. 

We've successfully added a brand new microservice to the Academix backend infrastructure, securely integrated with the database, auth service, and RBAC rules.

## What Was Built

### 1. Database Schema
We extended the single source of truth in `auth-service` to include:
- `AttendanceStatus` Enum (`PRESENT`, `ABSENT`, `LATE`, `HALF_DAY`, `EXCUSED`).
- `AttendanceRecord` model to track student daily attendance.
- Automatically generated and applied the Alembic migration to Postgres.

### 2. Microservice Scaffolding
- Bootstrapped `services/attendance-service` with the standard FastAPI structure.
- Re-used the shared `Dockerfile` and setup rules to integrate it seamlessly into the `docker-compose.dev.yml` stack.

### 3. Business Logic & Strict RBAC
The new endpoints in `http://localhost:8003/docs`:
- `POST /api/v1/attendance/daily`: Accepts an array of students and their statuses to mark attendance.
- **Authorization Rule:** Only the assigned `class_incharge` OR an active `substitute_teacher` (via `StaffDesignation`) can mark attendance for a class.
- **Edit Lock Rule:** Once a teacher marks attendance for the day, they are locked out from editing it. Only an Admin or the primary Class Incharge can overwrite an existing attendance record to fix mistakes.

## Verification
- ✅ **Alembic migrations** successfully applied.
- ✅ **Docker Container** `sms-attendance-dev` built and running.
- ✅ **Uvicorn Server** started cleanly without any dependency or import errors.

## Next Steps
You can head over to `http://localhost:8003/docs` and test out the new endpoints! 

1. Grab a token for **Teacher A** from the Auth Service (`:8000/docs`).
2. Authorize the Attendance Service.
3. Try to mark attendance for a class using the `POST` endpoint.
4. Try to re-submit it (it should block you).
5. Login as the **Admin** and edit it!
