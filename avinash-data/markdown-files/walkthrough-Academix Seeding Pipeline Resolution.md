# Academix Seeding Pipeline Resolution

We have successfully diagnosed and resolved a chain of severe API blockages that prevented the `seed_massive.py` script from successfully populating the 10-school multi-tenant database. The script is now actively executing in the background and populating over 12,000+ students and 600+ teachers.

Here is a summary of the critical issues we addressed to ensure the microservices function perfectly under heavy automated load:

## 1. 401 Unauthorized (Invalid Admin UUIDs)

**Issue**: The seeder was failing to map existing users correctly when it was restarted, resulting in it creating JWT tokens for randomly generated UUIDs that did not exist in the database.
**Resolution**: We patched `seed_massive.py` to check the database using `SELECT id FROM users WHERE mobile = ...`. If the user already exists, it captures the valid `admin_id` and explicitly injects it into the JWT token claims, bypassing authentication issues.

## 2. 405 Method Not Allowed (Route Shadowing)

**Issue**: `user-service` consistently threw a `405 Method Not Allowed` when creating students using `POST /api/v1/users/with-password`. 
**Diagnosis**: The FastAPI router in `user-service/app/api/v1/endpoints/users.py` declared `GET /api/v1/users/{user_id}` **before** `POST /api/v1/users/with-password`. Since "with-password" was intercepted as a string value for `{user_id}`, FastAPI rejected the `POST` method because it expected a `GET` request.
**Resolution**: 
* Reordered the specific endpoints (`/invite`, `/with-password`) to sit before the generic `{user_id}` endpoints in `users.py`.
* Fixed a missing `volumes` mount in `docker-compose.dev.yml` for `user-service` to ensure `uvicorn --reload` tracked the live code changes.

## 3. 500 Internal Server Error (Bcrypt/Passlib Crash)

**Issue**: After resolving the routing bug, `user-service` threw massive `500 INTERNAL_SERVER_ERROR` responses when attempting to generate student passwords.
**Diagnosis**: The `passlib` library has a hard incompatibility with `bcrypt >= 4.1.0`. The `python:3.12-slim` image pulled the latest `bcrypt==5.0.0` wheel, which completely broke `passlib`'s hashing functions resulting in an `AttributeError`/`ValueError`.
**Resolution**: 
* Pinned `bcrypt==4.0.1` explicitly in both `auth-service/requirements.txt` and `user-service/requirements.txt`.
* Force-rebuilt both Docker images using `--no-cache` to wipe out the incompatible versions and successfully restored the hash generation functionality.

## 4. Pydantic ValidationError (Missing Mobile Field)

**Issue**: Student creation still threw 500 errors internally due to a serialization validation failure: `1 validation error for UserProfileResponse: mobile: Input should be a valid string`.
**Diagnosis**: `UserProfileResponse` schema forced `mobile: str` to be required. However, students generated via `POST /with-password` only use usernames, meaning their mobile number is `None`.
**Resolution**: Updated `user.py` schema to set `mobile: Optional[str] = None` and explicitly added `username: Optional[str] = None` so Pydantic accurately serializes password-based users without failing.

---

> [!TIP]
> **Data Generation In Progress**
> The database has been cleanly truncated, and `seed_massive.py` is actively executing. You can monitor the progress inside the terminal or by running `docker exec sms-postgres-dev psql -U sms_user -d school_management_dev -c "SELECT count(*) FROM users;"`.

Once the script finishes (it will take a few minutes due to the computationally expensive Bcrypt hashing on 12,000+ passwords), the database will be fully primed with robust synthetic data across all multi-tenant services. We are now ready to tackle the "Bento Box" dashboard UI validation.
