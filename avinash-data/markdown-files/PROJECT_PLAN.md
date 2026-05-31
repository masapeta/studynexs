# AI-Powered School Management Platform
## Complete Project Plan & Technical Architecture

> **Version:** 1.0 | **Date:** April 2026 | **Status:** Phase 1 — In Progress
> **Pilot:** Single school on Azure Free Tier → **Production:** Multi-school SaaS

---

## Table of Contents

1. [Vision & Goals](#1-vision--goals)
2. [Tech Stack: Pilot vs Production](#2-tech-stack-pilot-vs-production)
3. [System Architecture](#3-system-architecture)
4. [Microservices Breakdown](#4-microservices-breakdown)
5. [Database Architecture](#5-database-architecture)
6. [AI Layer Architecture](#6-ai-layer-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Infrastructure & Environments](#8-infrastructure--environments)
9. [Phase-by-Phase Roadmap](#9-phase-by-phase-roadmap)
10. [API Design Contracts](#10-api-design-contracts)
11. [Current Status](#11-current-status)

---

## 1. Vision & Goals

### What We Are Building
A **production-grade, AI-native School Operating System** — not a traditional ERP.

| Traditional ERP | Our Platform |
|---|---|
| Stores data | Understands data |
| Manual reports | AI predictions |
| Teachers answer queries | AI tutors students 24/7 |
| Generic dashboards | Personalized student intelligence |
| No learning | Self-improving AI |

### Target Users
| Role | What They Get |
|---|---|
| **Student** | AI tutor, personalised study plan, doubt resolution, progress tracking |
| **Parent** | Real-time attendance, fee alerts, academic reports, teacher chat |
| **Teacher** | Auto-attendance, AI-generated lesson plans, question papers, chat with AI fallback |
| **Admin** | School operations, fee management, analytics dashboard |
| **Operations** | Transport, library, hostel management |

### Business Model
```
Phase 1 (Now)   → Single school pilot (FREE — prove value)
Phase 2         → 2–5 schools (₹5,000–10,000/school/month)
Phase 3         → 10+ schools (SaaS pricing — per student/per month)
Phase 4         → 50+ schools (Enterprise contracts)
```

---

## 2. Tech Stack: Pilot vs Production

> **Key principle:** Same codebase, swap infrastructure. No re-write ever.

### 2.1 Backend

| Component | Pilot (Azure Free) | Production (Scale) | Why |
|---|---|---|---|
| **Framework** | FastAPI (Python 3.12) | FastAPI (Python 3.12) | No change — async, fast, auto-docs |
| **Architecture** | Microservices (8 services) | Microservices (8 services) | No change |
| **Container** | Docker Compose | Azure Container Apps (ACA) | ACA = serverless containers, auto-scale |
| **API Gateway** | Nginx (Docker) | Azure API Management | Rate limiting, auth, analytics |
| **Runtime** | Local / Azure VM B2s | Azure Container Apps | No change |

### 2.2 Databases

| Database | Pilot | Production | What It Stores |
|---|---|---|---|
| **PostgreSQL** | Azure DB for PostgreSQL Flex — Free Tier (32GB, 1 vCore) | Azure DB for PostgreSQL Flex — Burstable B2ms or General Purpose | Users, schools, students, grades, attendance, fees |
| **MongoDB** | MongoDB Atlas M0 (Free, 512MB) | MongoDB Atlas M10+ | AI conversation history, session memory, agent logs |
| **Redis** | Azure Cache for Redis — Basic C0 (250MB) | Azure Cache for Redis — Standard C1 | OTP storage, JWT blacklist, LLM response cache, rate limits |
| **Qdrant** | Self-hosted Docker on Azure VM | Qdrant Cloud or AKS-hosted Qdrant | Vector embeddings for RAG, semantic search |

### 2.3 AI & LLM Layer

| Component | Pilot | Production | Notes |
|---|---|---|---|
| **Primary LLM** | Gemini 1.5 Pro (Google AI Pro API) | Gemini 1.5 Pro (Google AI Studio / Vertex AI) | Same model, different billing |
| **Secondary LLM** | Gemini 1.5 Flash (same API key) | Gemini 1.5 Flash | Cost/speed fallback |
| **Emergency LLM** | Ollama `gemma3:4b` (local, 2.5GB) | Not needed in prod | Internet outage safety net |
| **Embeddings** | `text-embedding-004` (Google AI) | `text-embedding-004` or `text-embedding-3-large` (OpenAI) | Converts text → vectors |
| **Vector Store** | Qdrant (Docker) | Qdrant Cloud | RAG knowledge retrieval |
| **AI Orchestration** | LangGraph + LangChain | LangGraph + LangChain | No change |
| **MCP** | mcp Python SDK (Phase 4.5) | mcp Python SDK | No change |
| **TTS** | edge-tts (free, no API key) | edge-tts | Microsoft Edge voices |
| **STT** | OpenAI Whisper (local) | Azure Speech Service | Phase 2 |
| **Image Analysis** | Gemini Vision | Gemini Vision | Phase 3 |

### 2.4 Frontend & Mobile

| Component | Pilot | Production | Notes |
|---|---|---|---|
| **Web App** | Next.js 14 (App Router) | Next.js 14 | No change |
| **Styling** | Tailwind CSS + shadcn/ui | Tailwind CSS + shadcn/ui | No change |
| **State Mgmt** | Zustand + React Query | Zustand + React Query | No change |
| **Mobile** | — (Phase 2) | Flutter 3.x | iOS + Android from single codebase |
| **CDN** | Azure Static Web Apps | Azure Static Web Apps + CDN | Auto SSL, global CDN |

### 2.5 Communication & Notifications

| Component | Pilot | Production | Notes |
|---|---|---|---|
| **OTP SMS** | MSG91 | MSG91 | India-first, UPI-friendly |
| **Push Notifications** | Firebase FCM | Firebase FCM | Free tier covers 10 schools |
| **Email** | SendGrid (100 emails/day free) | SendGrid (paid) | Alerts, reports |
| **In-app Chat** | WebSocket (FastAPI) | WebSocket + Redis Pub/Sub | Phase 3 |
| **WhatsApp** | — (Phase 6+) | Twilio WhatsApp API | After pilot proves value |
| **Real-time** | WebSocket | WebSocket | No change |

### 2.6 Storage

| Component | Pilot | Production | Notes |
|---|---|---|---|
| **File Storage** | Azure Blob Storage (5GB free) | Azure Blob Storage (paid) | Profile photos, documents, question papers |
| **CDN for files** | Azure CDN (basic) | Azure CDN | Fast file delivery |
| **Local dev** | MinIO (Docker, S3-compatible) | — | Only in dev environment |

### 2.7 DevOps & Infrastructure

| Component | Pilot | Production | Notes |
|---|---|---|---|
| **IaC** | Azure Bicep | Azure Bicep | Infrastructure as Code |
| **CI/CD** | GitHub Actions | GitHub Actions | No change |
| **Containers** | Docker Compose | Azure Container Apps | Auto-scaling in prod |
| **Secrets** | `.env.dev` file | Azure Key Vault | Never hardcode secrets |
| **Monitoring** | Console logs | Azure Monitor + Grafana | Phase 2 |
| **Logging** | structlog (JSON) | Azure Log Analytics + structlog | Same library, cloud sink |
| **Alerting** | — | Azure Alerts + PagerDuty | Production only |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│                                                                             │
│   Next.js Web App          Flutter Mobile          Admin Dashboard          │
│   (Student/Teacher/        (iOS + Android)         (Next.js)               │
│    Parent Portal)          Phase 2                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (Nginx / Azure APIM)                     │
│   • Rate limiting  • JWT validation  • Request routing  • Load balancing   │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬───────┘
   │          │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌──────────┐
│ auth │ │ user │ │academic  │ │ ai   │ │  comms   │ │school│ │analytics │
│  svc │ │  svc │ │   svc    │ │  svc │ │   svc    │ │  ops │ │   svc    │
│:8001 │ │:8002 │ │  :8003   │ │:8004 │ │  :8005   │ │:8006 │ │  :8007   │
└──┬───┘ └──┬───┘ └────┬─────┘ └──┬───┘ └────┬─────┘ └──┬───┘ └────┬─────┘
   │        │          │          │           │          │          │
   └──────────────────────────────┼───────────┘──────────┘──────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    │     DATA LAYER              │
                    │                             │
                    │  PostgreSQL  MongoDB  Redis │
                    │  (relational)(documents)(cache)│
                    │                             │
                    │  Qdrant       Azure Blob    │
                    │  (vectors)    (files)        │
                    └─────────────────────────────┘
```

### 3.2 Request Flow (Example: Student asks AI Tutor)

```
Student opens app
      │
      ├── 1. Next.js sends: POST /api/v1/ai/ask
      │         Header: Authorization: Bearer <JWT>
      │         Body: { "question": "Explain photosynthesis" }
      │
      ├── 2. Nginx (API Gateway) receives request
      │         → Rate limit check (60 req/min per IP)
      │         → Route to ai-service:8004
      │
      ├── 3. ai-service validates JWT
      │         → Extracts: user_id, school_id, role from token
      │
      ├── 4. Semantic Cache check (Redis + Qdrant)
      │         → "Has any student in this school asked this before?"
      │         → HIT: Return cached answer instantly (0 LLM cost)
      │         → MISS: Continue to LLM
      │
      ├── 5. RAG Retrieval (Qdrant)
      │         → Embed question → search vector store
      │         → Retrieve top 5 relevant textbook chunks
      │
      ├── 6. LLM Call (3-tier)
      │         → Try: Gemini 1.5 Pro API
      │         → Fallback: Gemini 1.5 Flash (if quota hit)
      │         → Emergency: Ollama gemma3:4b (if API down)
      │
      ├── 7. Store in semantic cache (Redis + Qdrant)
      │         → For future students asking similar questions
      │
      ├── 8. Store in MongoDB
      │         → AI session history for self-improving feedback loop
      │
      └── 9. Return response to student
                → Text answer + audio (edge-tts) if requested
```

---

## 4. Microservices Breakdown

### Service 1: auth-service (Port 8001) ✅ COMPLETE
**Responsibility:** OTP login, JWT tokens, RBAC

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/send-otp` | POST | Send OTP via MSG91 SMS |
| `/api/v1/auth/verify-otp` | POST | Verify OTP → return JWT + refresh token |
| `/api/v1/auth/refresh` | POST | Refresh token rotation |
| `/api/v1/auth/logout` | POST | Blacklist token + revoke refresh |
| `/api/v1/auth/me` | GET | Get current user profile |

**Database:** PostgreSQL (schools, users tables)
**Cache:** Redis (OTP storage, JWT blacklist, cooldowns)

---

### Service 2: user-service (Port 8002) — Phase 1b
**Responsibility:** User profiles, role management, onboarding

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/users/profile` | GET/PUT | View/update own profile |
| `/api/v1/users/` | GET | Admin: list all users |
| `/api/v1/users/{id}/role` | PUT | Admin: change user role |
| `/api/v1/users/students/{id}/parents` | POST | Link parent to student |
| `/api/v1/users/bulk-import` | POST | Excel import for mass onboarding |

**Database:** PostgreSQL (user_profiles, parent_student_links)
**Storage:** Azure Blob (profile photos)

---

### Service 3: academic-service (Port 8003) — Phase 2
**Responsibility:** Classes, subjects, attendance, grades, timetable

| Module | What it handles |
|---|---|
| Classes | Class creation, student enrollment, section management |
| Subjects | Subject-teacher mapping, syllabus tracking |
| Attendance | Daily marking, reports, alerts (< 75% triggers parent notification) |
| Grades | Marks entry, grade calculation, report cards |
| Timetable | Period scheduling, room allocation |
| Assignments | Creation, submission, AI grading (Phase 4) |
| Exams | Question paper management, seating arrangement |

**Database:** PostgreSQL (all academic tables)

---

### Service 4: ai-service (Port 8004) — Phase 4
**Responsibility:** All AI agents, RAG pipeline, semantic caching

| Agent | Purpose |
|---|---|
| **AI Tutor** | Answers student questions using RAG + Gemini |
| **Study Plan Agent** | Personalised weekly/monthly study plans |
| **Student Profiler** | 360° student intelligence (academic + cognitive) |
| **Lesson Plan Agent** | AI-generated lesson plans for teachers |
| **Question Paper Agent** | Auto-generate papers by chapter/difficulty/bloom |
| **Chat Fallback Agent** | Handles student-teacher chat when teacher is inactive 15+ min |
| **Alert Agent** | Proactive alerts (attendance, performance drops) |
| **Auto-grader** | AI grading for short/long answers (Phase 6) |

**Database:** MongoDB (AI sessions, agent memory, feedback loops)
**Cache:** Redis + Qdrant (semantic response cache)
**LLM:** Gemini 1.5 Pro → Flash → Ollama gemma3:4b

---

### Service 5: communication-service (Port 8005) — Phase 3
**Responsibility:** Real-time chat, notifications, announcements

| Feature | Technology |
|---|---|
| Real-time chat | WebSocket (FastAPI) |
| Message storage | MongoDB |
| Push notifications | Firebase FCM |
| SMS alerts | MSG91 |
| Email | SendGrid |
| WhatsApp | Phase 6+ |

**Smart Chat:** If teacher doesn't reply in 15 minutes → AI agent takes over silently → teacher gets summary when they return.

---

### Service 6: school-ops-service (Port 8006) — Phase 5
**Responsibility:** Fees, transport, library, events

| Module | Features |
|---|---|
| **Fees** | Fee structure setup, individual invoicing, Razorpay integration, receipt generation, overdue alerts |
| **Transport** | Route management, bus tracking, student-route mapping |
| **Library** | Book inventory, issue/return tracking, fine management |
| **Events** | Event calendar, circulars, holiday management |
| **Hostel** | Room allocation, mess management (if applicable) |

---

### Service 7: analytics-service (Port 8007) — Phase 5
**Responsibility:** Dashboards, reporting, predictive analytics

| Dashboard | Audience | Key Metrics |
|---|---|---|
| School Overview | Admin | Attendance %, fee collection, top/bottom performers |
| Student Report | Teacher/Parent | Subject-wise progress, attendance, AI interaction |
| Teacher Dashboard | Teacher | Class performance, pending tasks, AI suggestions |
| Dropout Risk | Admin | ML model predicting at-risk students |
| Gamification | Student | Points, badges, leaderboard (Phase 6) |

---

### Service 8: file-service (Port 8008) — Phase 1b
**Responsibility:** Azure Blob pre-signed URLs, file management

| Feature | Description |
|---|---|
| Upload | Generate pre-signed URL → client uploads directly to Azure Blob |
| Download | Generate time-limited download URL |
| Types supported | Images, PDFs, audio, video (question paper solutions) |

---

## 5. Database Architecture

### 5.1 PostgreSQL — Complete Schema

```
schools (Phase 1) ✅
├── id (UUID PK)
├── name
├── code (unique)
├── address (JSONB)
├── settings (JSONB) ← academic year, grading system, AI config
├── subscription_plan
└── is_active, created_at, updated_at

users (Phase 1) ✅
├── id (UUID PK)
├── school_id (FK → schools) ← EVERY table has this
├── mobile (unique)
├── email
├── full_name
├── role (student|parent|teacher|class_incharge|admin|operations)
├── profile_photo
├── preferred_language
├── notification_preferences (JSONB)
└── is_active, last_login_at, created_at, updated_at

── Phase 2 Tables ─────────────────────────────────────────────────────

academic_years
├── id, school_id, year_label (e.g. "2025-26")
├── start_date (April 1), end_date (March 31)
└── is_current

classes
├── id, school_id, academic_year_id
├── name (e.g. "Grade 10"), section (e.g. "A")
└── class_incharge_id (FK → users)

subjects
├── id, school_id, class_id
├── name, code
└── teacher_id (FK → users)

student_profiles
├── id, school_id, user_id (FK → users)
├── roll_number, admission_number
├── date_of_birth, gender
├── class_id (FK → classes)
└── parent_ids (ARRAY of UUIDs → users)

attendance
├── id, school_id, student_id, class_id
├── date, status (present|absent|late|half_day)
├── marked_by (teacher_id)
└── reason (if absent)

grades
├── id, school_id, student_id, subject_id
├── exam_type (unit_test|mid_term|final|assignment)
├── max_marks, obtained_marks, grade_letter
└── remarks, created_at

timetable
├── id, school_id, class_id, subject_id
├── day_of_week, period_number
├── start_time, end_time
└── room_number

── Phase 5 Tables ─────────────────────────────────────────────────────

fee_structures
├── id, school_id, class_id (nullable = school-wide)
├── fee_type, amount, frequency
└── academic_year_id

fee_records
├── id, school_id, student_id, fee_structure_id
├── amount_due, amount_paid, balance
├── status (pending|paid|overdue|partial)
├── due_date, paid_date
└── razorpay_payment_id

transport_routes
├── id, school_id, route_name
├── stops (JSONB array)
└── driver_id, vehicle_number

library_books
├── id, school_id, isbn, title, author
├── total_copies, available_copies
└── category, location

library_issues
├── id, school_id, book_id, user_id
├── issued_date, due_date, returned_date
└── fine_amount
```

### 5.2 MongoDB — Document Collections

```javascript
// ai_sessions — one doc per AI interaction
{
  _id: ObjectId,
  school_id: "uuid",
  student_id: "uuid",
  agent_type: "tutor" | "study_plan" | "chat_fallback",
  question: "Explain photosynthesis",
  context_retrieved: [...],      // RAG chunks used
  llm_used: "gemini-1.5-pro",
  response: "...",
  was_cached: false,
  tokens_used: 1200,
  response_time_ms: 1450,
  feedback: { rating: 4, teacher_override: false },
  created_at: ISODate
}

// agent_memory — persistent memory per student
{
  _id: ObjectId,
  school_id: "uuid",
  student_id: "uuid",
  memory_type: "long_term" | "working",
  content: {
    weak_topics: ["photosynthesis", "algebra"],
    learning_style: "visual",
    avg_session_duration: 22,
    preferred_explanation_depth: "detailed"
  },
  updated_at: ISODate
}

// self_improvement_logs — for AI quality tracking
{
  _id: ObjectId,
  school_id: "uuid",
  agent_type: "tutor",
  session_id: "...",
  metric: "teacher_override" | "student_disengagement" | "hallucination_flag",
  old_prompt_version: "v1.2",
  details: "...",
  created_at: ISODate
}
```

### 5.3 Qdrant — Vector Collections

```
Collections:
├── school_knowledge_{school_id}     ← textbooks, notes per school
├── question_bank_{school_id}        ← past questions + solutions
├── llm_response_cache               ← semantic response cache (all schools)
└── student_profiles_{school_id}     ← student learning embeddings
```

---

## 6. AI Layer Architecture

### 6.1 LLM Strategy (3-Tier)

```
Every AI request:
      │
      ▼
Tier 1: Gemini 1.5 Pro (Google AI API)
      │ Fails (timeout / 5xx)?
      ▼
      Tenacity: retry 2× with 1s backoff
      │ Still fails? Or 429 quota?
      ▼
Tier 2: Gemini 1.5 Flash (same API key, secondary model)
      │ Fails?
      ▼
Tier 3: Ollama gemma3:4b (localhost:11434)
        2.5GB, 4GB RAM, zero API cost
        Ultimate offline safety net
```

### 6.2 Semantic Caching (Cost Reduction)

```
Student 1: "What is photosynthesis?"
      │
      ├── Redis exact cache: MISS
      ├── Qdrant semantic: MISS (first ever)
      ├── Call Gemini 1.5 Pro → response
      ├── Store in Redis (exact key, 24h TTL)
      ├── Store in Qdrant (embedding, school scoped)
      └── Return response (~1.2s)

Student 2 (same school): "Explain photosynthesis to me"
      │
      ├── Redis exact: MISS (different wording)
      ├── Qdrant semantic: HIT (cosine similarity > 0.92)
      └── Return cached response (0 LLM cost, ~50ms) ✅

Student 3 (different school): "What is photosynthesis?"
      │
      ├── Check: same school_id? NO → treat as new query
      └── Call LLM (school data isolation guaranteed)
```

**Estimated savings:** 40–60% LLM API cost reduction at 100+ students/school

### 6.3 Self-Improving Agent System

```
AI responds to student
      │
      ├── Teacher reviews → agrees → log positive signal
      ├── Teacher overrides → log correction → update prompt template
      ├── Student disengages → log → adjust explanation depth
      └── Hallucination flagged → log → add to RAG rejection list

Monthly (automated):
      ├── Analyse feedback logs in MongoDB
      ├── Calculate: resolution rate, override rate, satisfaction score
      ├── Auto-tune: prompt templates, RAG retrieval threshold
      └── A/B test: new prompt vs old → promote winner
```

### 6.4 MCP (Model Context Protocol) — Phase 4.5

```
5 MCP Servers:
├── academic-mcp    → attendance, grades, timetable tools
├── student-mcp     → student profile, learning history tools
├── school-ops-mcp  → fee status, transport tools
├── communication-mcp → send notification, create alert tools
└── ai-memory-mcp   → agent memory read/write tools

AI Agent uses tools via MCP:
"Check if Ravi's attendance is below 75%"
      → ai-service calls academic-mcp tool
      → tool calls academic-service API
      → returns structured data to agent
      → agent generates alert
```

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
Mobile number entered
      │
      ├── POST /auth/send-otp
      │     → Rate limit: 3 OTPs/hour per mobile
      │     → Cooldown: 5 minutes between sends
      │     → OTP stored in Redis (5 min TTL)
      │     → SMS sent via MSG91
      │
      ├── POST /auth/verify-otp
      │     → Max 3 wrong attempts → OTP invalidated
      │     → On success: access token (15 min) + refresh token (30 days)
      │     → school_id embedded in JWT claims
      │     → Refresh token stored in Redis (opaque UUID)
      │
      ├── GET /api/... (authenticated request)
      │     → JWT decoded → signature verified
      │     → JTI checked against Redis blacklist
      │     → User loaded from PostgreSQL
      │
      └── POST /auth/logout
            → JTI added to Redis blacklist (TTL = remaining token life)
            → Refresh token deleted from Redis
```

### 7.2 RBAC (Role-Based Access Control)

```python
# Roles and what they can access:
Role            → Permitted Services
─────────────────────────────────────────────
student         → own profile, AI tutor, own grades/attendance
parent          → linked student's data, teacher chat, fee payment
teacher         → own class students, attendance marking, grade entry
class_incharge  → all teachers' data in class, reports
admin           → all school data, user management, fee setup
operations      → transport, library, hostel (no academic data)
super_admin     → all schools (Phase 2 SaaS)
```

### 7.3 Multi-Tenancy Isolation

```sql
-- Every API query enforces school_id from JWT (never from request):
SELECT * FROM students
WHERE school_id = current_user.school_id  -- from JWT, server-controlled
AND class_id = :class_id;

-- school_id is NEVER accepted from query params/body
-- It ALWAYS comes from the decoded JWT token
```

---

## 8. Infrastructure & Environments

### 8.1 Development (Your Laptop)

```
Docker Compose (infra/docker/docker-compose.dev.yml)
├── postgres:16-alpine    → localhost:5432
├── mongodb:7             → localhost:27017
├── redis:7-alpine        → localhost:6379
├── qdrant:v1.9.0         → localhost:6333
├── ollama                → localhost:11434
├── minio (S3-like)       → localhost:9000 (console: 9001)
└── nginx                 → localhost:80

Python services run LOCALLY (hot reload):
├── auth-service          → localhost:8001/docs
├── user-service          → localhost:8002/docs
└── (others added phase by phase)

Data stored: Docker named volumes on your laptop hard drive
Secrets: .env files (never committed to git)
```

### 8.2 Pilot (Azure Free Tier)

```
Azure Resource Group: school-management-system-pilot
│
├── Azure Database for PostgreSQL Flex (Free tier)
│     32GB storage, 1 vCore, automatic backups
│
├── MongoDB Atlas M0 (Free, 512MB)
│     Cloud-hosted, 3-node replica set
│
├── Azure Cache for Redis (Basic C0, 250MB)
│     OTP, JWT blacklist, LLM cache
│
├── Azure Container Apps
│     auth-service, user-service (Phase 1)
│     Each service: 0.5 vCPU, 1GB RAM (auto-scales to zero)
│
├── Azure Blob Storage (5GB free)
│     Profile photos, documents
│
└── Qdrant on Azure Container Instance
      1 vCPU, 2GB RAM, persistent volume

CI/CD: GitHub Actions → auto-deploy on merge to 'pilot' branch
Secrets: Azure Key Vault (injected as env vars at runtime)
```

### 8.3 Production (Paid Azure)

```
Azure Resource Group: school-management-system-prod
│
├── Azure Database for PostgreSQL Flex (General Purpose)
│     4 vCores, 16GB RAM, 256GB SSD, geo-redundant backup
│     High Availability: Standby replica (auto-failover)
│
├── MongoDB Atlas M10 (paid)
│     3-node replica set, 10GB storage, daily snapshots
│
├── Azure Cache for Redis (Standard C2)
│     6GB, 1 replica, 99.9% SLA
│
├── Azure Container Apps (all 8 services)
│     Auto-scaling: 1–10 instances per service
│     Min instances: 0 (scale to zero at night)
│
├── Azure API Management
│     Rate limiting, analytics, developer portal
│
├── Azure Blob Storage (LRS)
│     Unlimited files, CDN-backed
│
├── Qdrant Cloud or AKS-hosted
│     GPU-enabled node for fast vector search
│
├── Azure Key Vault
│     All secrets, auto-rotated
│
└── Azure Monitor + Grafana
      Logs, metrics, alerts, dashboards
```

### 8.4 Environment Comparison

| Feature | Dev (Laptop) | Pilot (Azure Free) | Production (Azure Paid) |
|---|---|---|---|
| PostgreSQL | Docker | Azure PG Free | Azure PG General Purpose |
| MongoDB | Docker | Atlas M0 | Atlas M10+ |
| Redis | Docker | Azure Cache C0 | Azure Cache C2 |
| File Storage | MinIO (Docker) | Azure Blob (5GB free) | Azure Blob (unlimited) |
| LLM | Gemini API + Ollama | Gemini API only | Gemini API + Vertex AI |
| Deployment | Docker Compose | Azure Container Apps | Azure Container Apps |
| Domain | localhost | pilot.yourschool.com | app.yourschool.com |
| SSL | None | Azure-provided | Azure-provided |
| Cost/month | ~₹0 | ~₹0 | ~₹8,000–25,000 |

---

## 9. Phase-by-Phase Roadmap

### Phase 1: Foundation ← WE ARE HERE
**Goal:** Auth working, database live, infrastructure stable

| Task | Status |
|---|---|
| Architecture design (HLD + LLD) | ✅ Done |
| Monorepo structure | ✅ Done |
| Docker Compose dev environment | ✅ Done |
| auth-service (OTP + JWT + RBAC) | ✅ Code written |
| Database migrations (schools + users) | ✅ Done |
| Integration test suite | ✅ Done |
| Fix Pydantic import error & start service | 🔄 In progress |
| Swagger UI smoke test | ⏳ Next |
| Run test suite | ⏳ Next |

**Exit criteria:** auth-service running, all 16 tests pass, JWT flow verified

---

### Phase 1b: User Service + Azure Setup
**Goal:** User profiles + move to Azure

| Task | Est. Time |
|---|---|
| user-service full implementation | 3–4 days |
| Parent ↔ Student linking | 1 day |
| Profile photo upload (Azure Blob) | 1 day |
| Bulk user import (Excel) | 2 days |
| Azure PostgreSQL Flex setup | 1 day |
| GitHub Actions CI/CD pipeline | 1 day |
| Deploy to Azure Container Apps | 2 days |

---

### Phase 2: Academic Core
**Goal:** Full academic management

| Module | Est. Time |
|---|---|
| Classes + Sections management | 3 days |
| Subject + Teacher mapping | 2 days |
| Attendance marking + reports | 4 days |
| Grades + Report cards | 4 days |
| Timetable management | 3 days |
| Academic year management | 2 days |

---

### Phase 3: Communication System
**Goal:** Real-time chat + notifications

| Module | Est. Time |
|---|---|
| WebSocket real-time chat | 4 days |
| AI fallback (15-min threshold) | 3 days |
| Push notifications (FCM) | 2 days |
| SMS alerts (MSG91) | 1 day |
| Announcement/circular system | 2 days |
| Chat history + search | 2 days |

---

### Phase 4: AI Core
**Goal:** Full AI tutor + student intelligence

| Module | Est. Time |
|---|---|
| RAG pipeline (Qdrant + embeddings) | 5 days |
| AI Tutor agent (LangGraph) | 5 days |
| Study Plan agent | 3 days |
| Student Profiler | 4 days |
| Semantic caching (Redis + Qdrant) | 3 days |
| Self-improving feedback loop | 4 days |
| edge-tts integration | 1 day |

---

### Phase 4.5: MCP Integration
**Goal:** Standardise AI tool access

| Task | Est. Time |
|---|---|
| 5 MCP servers implementation | 5 days |
| LangChain MCP adapter integration | 2 days |
| Tool testing + observability | 2 days |

---

### Phase 5: Operations
**Goal:** Full school operations

| Module | Est. Time |
|---|---|
| Fee management + Razorpay | 5 days |
| Transport management | 3 days |
| Library management | 3 days |
| Analytics dashboards | 5 days |
| Predictive analytics (dropout risk) | 4 days |
| Gamification (points + badges) | 3 days |

---

### Phase 6+: Scale & Advanced AI
**Goal:** Enterprise SaaS

| Feature | Description |
|---|---|
| Multi-tenancy SaaS | Super-admin, school onboarding portal |
| WhatsApp integration | Twilio WhatsApp Business API |
| Auto-grading | AI grades short/long answer questions |
| Question paper generator | Full syllabus-mapped paper generation |
| AI report cards | Auto-generated narrative report cards |
| Parent app (Flutter) | Dedicated parent mobile experience |
| Offline mode | PWA + local sync for low connectivity |

---

## 10. API Design Contracts

### Standard Response Format (all APIs)

```json
// Success
{
  "success": true,
  "data": { ... },
  "meta": null,
  "timestamp": "2026-04-21T11:00:00Z"
}

// Error
{
  "success": false,
  "error": {
    "code": "OTP_RATE_LIMITED",
    "message": "Please wait 240 seconds before requesting another OTP",
    "details": { "retry_after": 240 }
  },
  "timestamp": "2026-04-21T11:00:00Z"
}

// Paginated
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 450,
    "total_pages": 23
  }
}
```

### Error Code Registry

| Code | HTTP Status | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request body failed validation |
| `OTP_RATE_LIMITED` | 429 | Too many OTP requests |
| `OTP_INVALID` | 401 | Wrong OTP submitted |
| `OTP_EXPIRED` | 400 | OTP has expired |
| `TOKEN_INVALID` | 401 | JWT invalid or expired |
| `TOKEN_BLACKLISTED` | 401 | Token was logged out |
| `REFRESH_TOKEN_INVALID` | 401 | Refresh token expired |
| `INSUFFICIENT_ROLE` | 403 | User role not allowed |
| `ACCOUNT_DEACTIVATED` | 403 | School admin deactivated user |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

---

## 11. Current Status

### ✅ Completed (Phase 1)
- [x] Architecture v1.2 (HLD + LLD)
- [x] Monorepo structure (8 services scaffold)
- [x] Docker Compose dev environment (PostgreSQL, Redis, Qdrant, MongoDB, MinIO, Nginx)
- [x] Nginx API gateway (rate limiting, routing)
- [x] Shared constants and enums
- [x] auth-service — 18 production files
  - [x] OTP service (MSG91 + Redis rate limiting, dev fallback)
  - [x] JWT security (access + opaque refresh + blacklist)
  - [x] RBAC (`require_roles()` dependency factory)
  - [x] 5 API endpoints (send-otp, verify-otp, refresh, logout, /me)
  - [x] Alembic migrations (schools + users tables)
  - [x] 16 integration tests
- [x] Database migrations run successfully
- [x] 3-tier LLM strategy (Pro → Flash → Ollama gemma3:4b)
- [x] Semantic cache design

### 🔄 In Progress
- [ ] Fix Pydantic `ConfigDict` import → start uvicorn → smoke test
- [ ] Run test suite (pytest)

### ⏳ Next Up (Phase 1b)
- [ ] user-service full implementation
- [ ] Azure PostgreSQL setup
- [ ] GitHub Actions CI/CD
- [ ] Deploy to Azure Container Apps

---

*Document maintained by the engineering team. Update after each phase completion.*
