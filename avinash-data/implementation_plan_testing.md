# Backend Full Testing Plan

The objective is to achieve comprehensive testing of the Academix backend, covering functional, performance, security, and API integrity as per the requested standards.

## Proposed Testing Suite

### 1. Functional & API Testing (Pytest)
Expand the existing `pytest` suite to cover:
- **Fees Module**: Enrollment to collection, receipt generation, and status updates.
- **Attendance Module**: Marking daily/subject attendance and retrieval.
- **Academic Module**: Classes, Sections, and Subjects CRUD.
- **File Service**: Uploading, categorical storage, and metadata validation.
- **Notifications**: Triggering and batch-marking as read.

### 2. Performance Testing (Locust)
Implement a `locustfile.py` to simulate real-world traffic:
- **Load Testing**: 100 concurrent users performing common actions (login, view students, view fees).
- **Spike Testing**: Sudden bursts of requests to auth and search endpoints.

### 3. Security Testing (Custom Scripts & Manual Audit)
- **Injection Checks**: Verify that all parameters are safely handled by the ORM (SQLi).
- **Auth Bypass**: Test unauthorized access to protected routes.
- **RBAC Validation**: Ensure Teachers cannot access Super Admin features.

### 4. Database Integrity Testing
- **Transaction Rollbacks**: Verify that failed operations don't leave partial data.
- **Tenant Isolation**: Ensure data from one `school_id` never leaks to another.

## Proposed Changes

### [NEW] [test_fees.py](file:///c:/Users/avina/Documents/Projects/academix-platform/apps/api/tests/test_fees.py)
Detailed tests for fee structures, payments, and receipts.

### [NEW] [test_attendance.py](file:///c:/Users/avina/Documents/Projects/academix-platform/apps/api/tests/test_attendance.py)
Detailed tests for attendance marking and reporting.

### [NEW] [locustfile.py](file:///c:/Users/avina/Documents/Projects/academix-platform/apps/api/locustfile.py)
Performance test script.

### [MODIFY] [conftest.py](file:///c:/Users/avina/Documents/Projects/academix-platform/apps/api/tests/conftest.py)
Add more fixtures for common entities (Students, Classes).

## Verification Plan

### Automated Tests
- Run full suite: `pytest apps/api/tests/ --cov=app`
- Run load tests: `locust -f apps/api/locustfile.py --headless -u 100 -r 10 -t 1m`

### Security Audit
- Run a scan script on all POST/PUT routes to check for injection vulnerabilities.
