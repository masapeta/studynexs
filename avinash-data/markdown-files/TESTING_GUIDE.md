# 🧪 Academix Testing Guide (Docker Environment)

This guide walks you through end-to-end manual testing for the new **Floors** and **Designations** (Floor Incharge, Substitute Teacher) features using your local Docker setup.

## 🚀 1. Setup & Starting Services
All services (Auth, User, Academic, Postgres, Redis) are containerized.

**Start the stack:**
```powershell
docker compose -f infra/docker/docker-compose.dev.yml up -d
```

**View live logs:**
```powershell
docker compose -f infra/docker/docker-compose.dev.yml logs -f auth-service user-service academic-service
```

---

## 🔑 2. Login & Get User IDs
> **Swagger URLs:**
> - Auth Service: http://localhost:8000/docs
> - User Service: http://localhost:8001/docs
> - Academic Service: http://localhost:8002/docs

### A. Get Admin Token
1. Go to **Auth Service** (`:8000/docs`).
2. Run `POST /api/v1/auth/send-otp` with `{"mobile_number": "+919800000002"}` (Admin user).
3. Run `POST /api/v1/auth/verify-otp` with the OTP printed in your Docker logs.
4. Copy the `access_token` from the response.

### B. Authorize Swagger
1. Go to **Academic Service** (`:8002/docs`).
2. Click the green **Authorize** button at the top right.
3. Paste your token (just the token, no "Bearer " prefix).

### C. Find User IDs for Testing
You will need user IDs for testing designations. Go to **User Service** (`:8001/docs`), authorize, and run `GET /api/v1/users` to find these IDs (save them to a notepad):
- Teacher A (e.g., `+919800000003`) -> `teacher_id`
- Teacher B (Ravi, `+919800000004`) -> `floor_incharge_user_id`
- Teacher C (Deepak, `+919800000006`) -> `substitute_user_id`
- Student (`+919800000007`) -> `student_user_id`
- Parent (`+919800000008`) -> `parent_user_id`

---

## 📅 3. Academic Structure (Prerequisites)
Run these endpoints on **Academic Service** (`:8002/docs`):

1. **Create Academic Year:** `POST /api/v1/academic-years`
   ```json
   { "year_label": "2024-2025", "start_date": "2024-04-01", "end_date": "2025-03-31", "is_active": true }
   ```
   *(Copy the `id` -> `year_id`)*

2. **Create Class:** `POST /api/v1/classes`
   ```json
   { "grade": "Grade 5", "section": "A", "academic_year_id": "<year_id>" }
   ```
   *(Copy the `id` -> `class_id`)*

---

## 🏢 4. Testing Floors
1. **Create Ground Floor:** `POST /api/v1/floors`
   ```json
   { "name": "Ground Floor", "floor_number": 0 }
   ```
   *(Copy the `id` -> `floor_id`)*

2. **Assign Class to Floor:** `POST /api/v1/floors/{floor_id}/classes`
   ```json
   { "class_id": "<class_id>" }
   ```

3. **Verify:** `GET /api/v1/floors/{floor_id}/classes` -> Should return Grade 5A.

---

## 👨‍🏫 5. Testing Teachers & Students
1. **Enroll Teacher:** `POST /api/v1/teachers`
   ```json
   { "user_id": "<teacher_id>", "employee_id": "EMP001" }
   ```

2. **Create Subject:** `POST /api/v1/subjects`
   ```json
   { "name": "Mathematics", "class_id": "<class_id>", "teacher_id": "<teacher_id>" }
   ```

3. **Enroll Student:** `POST /api/v1/students`
   ```json
   { "user_id": "<student_user_id>", "admission_no": "ADM-001", "class_id": "<class_id>" }
   ```

4. **Link Parent:** `POST /api/v1/students/{student_id}/parents`
   ```json
   { "parent_user_id": "<parent_user_id>", "is_primary": true }
   ```

---

## 🏷️ 6. Testing Designations
1. **Assign Floor Incharge:** `POST /api/v1/designations`
   ```json
   {
     "user_id": "<floor_incharge_user_id>",
     "designation": "floor_incharge",
     "entity_type": "floor",
     "entity_id": "<floor_id>"
   }
   ```

2. **Assign Substitute Teacher:** `POST /api/v1/designations`
   ```json
   {
     "user_id": "<substitute_user_id>",
     "designation": "substitute_teacher",
     "entity_type": "class",
     "entity_id": "<class_id>",
     "start_date": "2024-06-01",
     "end_date": "2024-06-15"
   }
   ```

3. **Test Conflict Logic:** Run the EXACT SAME substitute request above but change the `user_id` to a different teacher. It should return a **409 Conflict** error.

4. **Revoke Designation:** `DELETE /api/v1/designations/{designation_id}` -> Soft deletes the assignment.

---

## 🔐 7. Testing RBAC Controls
1. Log out of Swagger by clicking **Authorize** -> **Logout**.
2. Go to **Auth Service**, get an OTP for the **Student** (`+919800000007`), and get their token.
3. Authorize **Academic Service** with the student token.
4. Try to create a Floor (`POST /api/v1/floors`).
5. **Expected Result:** You will get a `403 Forbidden` error because students don't have Admin permissions.
