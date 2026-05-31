# Massive Synthetic Data Seeding Plan

The goal is to scale up the synthetic data generation to simulate a multi-tenant environment with 10 fully operational schools, including heavy loads of classes, students, staff, and teacher mappings.

## User Review Required

> [!WARNING]  
> **Performance & Database Size**
> Generating 12,000+ students and their associated attendance/fee records is a large operation. Doing this via synchronous API calls would take hours. I will write a high-performance **Asynchronous (asyncio)** Python script to blast these API requests concurrently (e.g., 50-100 requests per second) to complete the seeding in a few minutes.

> [!IMPORTANT]
> **Clean Slate vs. Append**
> This script will create 10 brand new schools alongside your existing data. If you want a completely fresh start before running this, you can run `docker compose down -v` to wipe the DB, but it's not strictly necessary. The script will simply create 10 new school instances.

## Proposed Changes

### [NEW] `scripts/seed_massive.py`
A new async Python script using `httpx.AsyncClient` and `asyncio.Semaphore`.

**Data Generation Scope (Per School):**
- **Admins:** 1 to 3 admins.
- **Incharges:** 5 to 10 incharges.
- **Classes:** Grade 1 to 10. Sections A, B, C, D (40 classes total).
- **Students:** 30 students per class (1,200 students per school). Total: 12,000 students across 10 schools.
- **Parents:** Generated dynamically. We will group students by last name or randomly pick 1-3 children per parent.
- **Teachers:** We will generate a large pool of teachers (~60-80 per school). For each class and subject, we will map 1-2 teachers specifically to ensure there is "no shortfall" and everyone is fully covered.
- **Subjects:** Standard core subjects (Math, Science, English, History, etc.) assigned to all classes.
- **Hours:** 8:30 AM - 5:00 PM logic. (We'll store this in the school's configuration if supported, or ensure the synthetic attendance aligns with it).

## Verification Plan
1. Run the async script locally.
2. Monitor Docker container logs to ensure the APIs can handle the concurrent load without crashing.
3. Validate in the database: `SELECT school_id, COUNT(*) FROM students GROUP BY school_id;` (Should show ~1200 per school).
4. Log into the frontend using one of the newly generated Admin or Teacher credentials to verify the dashboard performance with heavy data.
