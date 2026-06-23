# 🎓 StudyNexs Platform

> AI-powered School Management System — Production-grade SaaS for K-8 schools.

![StudyNexs](assets/Logo.png)

**Documentation:** [Product bible](docs/PRODUCT.md) · [Build status](docs/STATUS.md)

---

## Architecture

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.11) — Modular Monolith |
| **Database** | PostgreSQL 16 + JSONB |
| **Cache / Auth** | Redis 7 (OTP, JWT blacklist, user cache) |
| **Vector DB** | Qdrant (RAG, semantic cache) |
| **Frontend** | Next.js 16 — admin-web (others planned) |
| **Gateway** | Nginx (rate limiting, proxy) |
| **Storage** | Azure Blob (PDFs, receipts, documents) |
| **CI/CD** | GitHub Actions → Azure Container Apps |

## Multi-Tenant Model

Each school gets a **subdomain**:
- `sia.studynexs.com` → Sunrise International Academy
- `gvps.studynexs.com` → Green Valley Public School

Tenant isolation is enforced at the database level (`school_id` on every row).

## Repository Structure

```
studynexs-platform/
├── apps/
│   ├── api/                 # FastAPI backend (modular monolith)
│   │   ├── app/core/        # Config, DB, Security, Tenant, Dependencies
│   │   ├── app/db/models/   # 16 SQLAlchemy models
│   │   ├── app/modules/     # 13 domain modules
│   │   ├── app/shared/      # Common schemas, pagination
│   │   ├── app/workers/     # Outbox relay, background tasks
│   │   ├── alembic/         # Database migrations
│   │   └── scripts/         # Seed data, utilities
│   ├── admin-web/           # School admin portal (built)
│   ├── teacher-web/         # Teacher portal (planned)
│   ├── parent-web/          # Parent portal (planned)
│   ├── student-web/         # Student portal (planned)
│   └── platform-web/        # SaaS operator console (planned)
├── infra/
│   ├── docker/              # docker-compose.dev.yml
│   ├── nginx/               # Gateway config
│   └── azure/               # Bicep IaC
├── docs/                    # ADRs, runbook, code graph
└── assets/                  # Logo, brand assets
```

## Portals

| Portal | Roles | Description |
|--------|-------|-------------|
| **admin-web** | admin, super_admin | Dashboard, students, staff, classes, fees, settings |
| **teacher-web** | teacher, class_incharge | Attendance, grades, timetable, report cards |
| **parent-web** | parent | Fee payment, attendance, report cards, notices |
| **student-web** | student | Timetable, marks, AI tutor, diary |
| **platform-web** | platform_operator | School onboarding, subscriptions, audit |

## Quick Start (Development)

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 20+

### 1. Start Infrastructure
```bash
docker compose -f infra/docker/docker-compose.dev.yml up -d
```

### 2. Run API (Local Development)
```bash
cd apps/api
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Seed Data
```bash
cd apps/api
python scripts/seed_synthetic.py
```

### 4. Access
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## Security

- JWT access tokens (15 min, in-memory only)
- HttpOnly refresh cookies (30 day, path-scoped)
- Redis token blacklist
- OTP: 5-min TTL, max 3 attempts, 5-min cooldown
- bcrypt cost 12, fail-secure
- Nginx rate limiting (auth: 30 req/min, API: 100 req/min)
- Tenant isolation enforced on every DB query
- Production guardrails: app crashes on boot if misconfigured

## License

Proprietary — © 2026 StudyNexs. All rights reserved.
