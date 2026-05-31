# Student Username/Password Auth Feature

We have successfully implemented the alternative login approach for students (and any other users who don't have mobile numbers)! The core database identity model has been fundamentally upgraded to support this.

## What Was Built

### 1. Database Schema Changes
The central `users` table in `auth-service` has been modified:
- `mobile` is no longer strictly mandatory.
- Added `username` (unique) and `password_hash`.
- A database-level `CheckConstraint` was added to guarantee that every user must have *either* a mobile number OR a username to exist in the system.

### 2. User Service Updates
We added a new endpoint for school Admins to create student accounts.
- **Endpoint:** `POST :8001/api/v1/users/with-password`
- **Logic:** The Admin provides a `first_name`, `last_name`, and a `password`. The system automatically generates the username using the requested format: `firstname.lastname`.
- **Deduplication:** If `ravi.kumar` already exists, the system automatically assigns `ravi.kumar1`, then `ravi.kumar2`, ensuring no collisions.

### 3. Auth Service Updates
We added a secure password authentication flow using industry-standard `bcrypt` hashing.
- **Endpoint:** `POST :8000/api/v1/auth/login-password`
- **Logic:** Accepts `username` and `password`. Validates the hash and returns the exact same JWT `TokenPair` as the OTP flow. This means the rest of the application (User Service, Academic Service, Attendance) requires zero changes to understand the student's token!

## Verification Steps
You can test this flow entirely locally via the Swagger UIs:

1. **Create the Student:**
   - Log into `http://localhost:8000/docs` using the Super Admin OTP (`+919800000001`).
   - Open `http://localhost:8001/docs` (User Service) and authorize using the token.
   - Hit `POST /api/v1/users/with-password` with:
     ```json
     {
       "first_name": "Ravi",
       "last_name": "Kumar",
       "password": "SecurePassword123!",
       "role": "student"
     }
     ```
   - Notice the response auto-generates the username `ravi.kumar`.

2. **Login as the Student:**
   - Go back to `http://localhost:8000/docs` (Auth Service).
   - Hit `POST /api/v1/auth/login-password` with `username: ravi.kumar` and your password.
   - You will successfully receive your JWT tokens!
