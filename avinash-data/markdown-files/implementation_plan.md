# AI-Powered School Management Platform — Architecture Design
## HLD + LLD | Phase 1 Architecture

> **Status**: Draft — Awaiting User Review & Approval
> **Version**: 1.2 (Azure Infra + edge-tts + Semantic Cache + Self-Improving AI + 3 Environments)
> **Architect**: Senior AI Architect + Principal Engineer

---

## 1. Executive Summary

We are building a **single-school-first, AI-native School Management Platform** designed to scale to multi-tenancy (SaaS) without schema migration.

**Key Design Decisions Summary:**

| Decision | Choice | Reason |
|---|---|---|
| Architecture Pattern | Microservices (7 core services) | Scalable, team-parallelizable |
| Web Frontend | Next.js 14 (App Router) | SSR, role-based routing, production-grade |
| Mobile | Flutter (Phase 2) | After web APIs are stable |
| Backend | FastAPI (Python) | Team strength, async, fast |
| Primary LLM | Google Gemini 1.5 Pro | Cost-effective, India-friendly |
| Fallback LLM | Ollama (`gemma4:31b-cloud`) | Self-hosted Google Gemma 4 31B, zero cost fallback |
| **AI Tool Layer** | **MCP (Model Context Protocol)** | **Standardized, LLM-agnostic tool interface (Phase 4.5)** |
| Auth | OTP via MSG91 + JWT | India-first, mobile-centric |
| Payments | Razorpay | India-first, UPI support |
| Notifications | FCM + MSG91 + WhatsApp Business API | Maximum India reach |
| API Gateway | Nginx (Phase 1) → Kong (Phase 2) | Pragmatic start |
| Async Queue | Redis Streams + Celery (Phase 1) → Kafka (Phase 2) | Avoid over-engineering |
| Primary DB | PostgreSQL | Structured school data |
| Secondary DB | MongoDB | Chat, AI profiles, logs |
| Vector DB | Qdrant (self-hosted) | RAG, student profiling |
| Cache | Redis | Sessions, real-time, caching |
| File Storage | Azure Blob Storage + Azure CDN | Free tier, pilot-friendly |
| Infra | Docker Compose (Dev/Test) → Azure Container Apps/AKS (Prod) | Azure-native, free tier start |

---

## 2. High-Level Architecture (HLD)

### 2.1 Architecture Principles

1. **School-ID First**: Every entity carries `school_id` from Day 1, enabling zero-migration multi-tenancy later.
2. **AI as Infrastructure**: AI is not a feature — it's embedded at every service layer.
3. **Async by Default**: All heavy operations (AI, reports, grading) are async via queues.
4. **Fail-Safe Communication**: Human-first, AI-fallback. AI never blocks the system.
5. **Role-Isolated Experiences**: Each role (student/parent/teacher/admin) gets a completely separate UI and API surface.
6. **Observability First**: Logs, traces, and metrics from Day 1 (not retrofitted).
7. **India-Optimized**: OTP auth, Razorpay, WhatsApp, regional language support (Unicode).

---

### 2.2 System Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│  ┌─────────────────────┐      ┌─────────────────────────────────┐ │
│  │   Next.js Web App   │      │     Flutter Mobile App (Ph2)    │ │
│  │  (Admin/Teacher/    │      │   (Student / Parent / Teacher)  │ │
│  │   Parent portal)    │      │                                 │ │
│  └──────────┬──────────┘      └──────────────┬──────────────────┘ │
└─────────────┼────────────────────────────────┼────────────────────┘
              │ HTTPS / WSS                     │ HTTPS / WSS
┌─────────────▼────────────────────────────────▼────────────────────┐
│                    NGINX (Reverse Proxy / API Gateway)             │
│        Rate Limiting │ SSL Termination │ Request Routing           │
│        Load Balancing │ Static File Serving                        │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                     SERVICE MESH (Internal Network)                │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ auth-service │  │ user-service │  │    academic-service       │ │
│  │              │  │              │  │ (students, subjects,      │ │
│  │ OTP/JWT/RBAC │  │ All profiles │  │  attendance, grades,      │ │
│  └──────────────┘  └──────────────┘  │  assignments, exams)      │ │
│                                      └──────────────────────────┘ │
│  ┌──────────────────────┐  ┌─────────────────────────────────────┐│
│  │ communication-service│  │         ai-service                  ││
│  │                      │  │  (LangGraph agents, RAG tutor,      ││
│  │ Chat (WebSocket)     │  │   profiling, study plans,           ││
│  │ AI Fallback Logic    │  │   lesson plans, grading, alerts)    ││
│  │ Escalation Manager   │  └─────────────────────────────────────┘│
│  └──────────────────────┘                                          │
│  ┌──────────────────────┐  ┌─────────────────────────────────────┐│
│  │  school-ops-service  │  │      analytics-service              ││
│  │                      │  │                                     ││
│  │  Fee (Razorpay)      │  │  Dashboards, Predictive AI,         ││
│  │  Transport           │  │  Reports, Risk Alerts               ││
│  │  Library             │  └─────────────────────────────────────┘│
│  │  Events / Notices    │                                          │
│  │  Timetable           │  ┌─────────────────────────────────────┐│
│  └──────────────────────┘  │       file-service                  ││
│                             │  S3 upload, pre-signed URLs,        ││
│                             │  CDN management                     ││
│                             └─────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
              │                    │                   │
┌─────────────▼──────┐  ┌─────────▼────────┐  ┌──────▼──────────────┐
│   DATA LAYER        │  │   CACHE / QUEUE  │  │   AI INFRA LAYER    │
│                     │  │                  │  │                     │
│  PostgreSQL         │  │  Redis           │  │  Qdrant (Vector DB) │
│  (Primary RDBMS)    │  │  - Sessions      │  │  Ollama (LLM host)  │
│                     │  │  - Cache         │  │  Gemini API         │
│  MongoDB            │  │  - WS Pub/Sub    │  │  S3 (files)         │
│  (Chat, AI logs,    │  │  - Rate limits   │  │  CloudFront (CDN)   │
│   profiles, diary)  │  │                  │  │                     │
│                     │  │  Celery Workers  │  │                     │
│                     │  │  (Async Tasks)   │  │                     │
└─────────────────────┘  └──────────────────┘  └─────────────────────┘

              ┌──────────────────────────────────────────────┐
              │         MCP LAYER  (Phase 4.5)               │
              │   Standardized Tool Interface for AI Agents  │
              │                                              │
              │  ┌──────────────────┐ ┌──────────────────┐  │
              │  │school-data-mcp   │ │ syllabus-mcp     │  │
              │  │(student/grades/  │ │ (RAG + Qdrant    │  │
              │  │ attendance/class)│ │  query tools)    │  │
              │  └──────────────────┘ └──────────────────┘  │
              │  ┌──────────────────┐ ┌──────────────────┐  │
              │  │academic-mcp      │ │ analytics-mcp    │  │
              │  │(assignments/exams│ │ (reports/risk/   │  │
              │  │ question bank)   │ │  dashboards)     │  │
              │  └──────────────────┘ └──────────────────┘  │
              │  ┌──────────────────────────────────────┐    │
              │  │ operations-mcp                       │    │
              │  │ (fee/transport/library/events)       │    │
              │  └──────────────────────────────────────┘    │
              │                                              │
              │  Consumed by: LangGraph Agents │ Claude      │
              │              Desktop │ Future AI Clients     │
              └──────────────────────────────────────────────┘
```

---

### 2.3 Service Responsibilities (7 Core Services)

| Service | Responsibility | Key APIs |
|---|---|---|
| **auth-service** | OTP login, JWT issue/refresh, RBAC enforcement | `/auth/send-otp`, `/auth/verify-otp`, `/auth/refresh`, `/auth/logout` |
| **user-service** | Profiles for all roles, onboarding | `/users`, `/students`, `/teachers`, `/parents` |
| **academic-service** | Subjects, attendance, grades, assignments, exams, timetable | `/attendance`, `/grades`, `/assignments`, `/exams`, `/timetable` |
| **communication-service** | Structured chat rooms, WebSocket, AI fallback, escalation, push notifications | `/chat/rooms`, `/chat/messages`, `WS /ws/chat/{room_id}` |
| **ai-service** | All AI agents (tutor, profiler, planner, grader, alert) | `/ai/tutor/ask`, `/ai/profile/{student_id}`, `/ai/study-plan`, `/ai/lesson-plan`, `/ai/grade` |
| **school-ops-service** | Fee, transport, library, events, notices, timetable | `/fees`, `/transport`, `/library`, `/events`, `/notices` |
| **analytics-service** | Dashboards, reports, predictive risk | `/analytics/student/{id}`, `/analytics/class/{id}`, `/analytics/reports` |
| **file-service** | Pre-signed S3 URLs, file metadata | `/files/upload-url`, `/files/metadata` |

---

### 2.4 Data Flow Diagrams

#### Flow 1: Student Asks a Doubt (AI Tutor)
```
Student App
    │─── POST /ai/tutor/ask ──────────────────────────────────▶  ai-service
                                                                       │
                                                           Celery task created
                                                                       │
                                                              RAG query (Qdrant)
                                                                       │
                                                          Retrieve syllabus context
                                                                       │
                                                         LLM (Gemini) generates answer
                                                                       │
                                                    [If Gemini fails] → Ollama fallback
                                                                       │
    Student App ◀─── Streamed response (SSE) ───────────────────────────
                                                                       │
                                                     MongoDB: Save to ai_session_logs
                                                                       │
                                                     Redis: Update student weakness cache
```

---

#### Flow 2: Chat with AI Fallback + Escalation
```
Student sends message
    │──▶ communication-service (WebSocket)
             │
             ├── Save to MongoDB (chat_messages)
             ├── Notify Teacher (FCM push)
             └── Celery: Schedule check_teacher_response(delay=15min)
                                │
                          After 15 minutes:
                                │
                    Teacher responded? ──YES──▶ Cancel task, done
                                │
                               NO
                                │
                    Classify message (ai-service)
                                │
                    ├── Academic? ──▶ AI generates step-by-step response
                    │                  Based on student profile + syllabus
                    │
                    └── Non-Academic? ──▶ "I'll notify your teacher"
                                          + Escalate to class in-charge (FCM)
                                          + Reminder to teacher
                                          + If still no response → Admin alert
```

---

#### Flow 3: Fee Payment (Razorpay)
```
Admin creates fee structure
    │──▶ school-ops-service ──▶ PostgreSQL (fee_structures)
                                        │
                                 Celery: Schedule due-date reminders
                                        │
Parent initiates payment
    │──▶ school-ops-service
             │──▶ Razorpay: Create order ──▶ Returns order_id
             │
    Parent completes payment (Razorpay checkout on frontend)
             │
    Razorpay Webhook ──▶ school-ops-service /webhooks/razorpay
             │
             ├── Verify signature
             ├── Update PostgreSQL (fees table: status = PAID)
             ├── Generate receipt (PDF via file-service -> S3)
             └── Notify parent (MSG91 SMS + WhatsApp)
```

---

#### Flow 4: AI Student Profile Generation (Background)
```
Trigger: End of day / Weekly cron (Celery Beat)
    │
    ├── Fetch: Grades, attendance, assignments, AI session logs (PostgreSQL + MongoDB)
    │
    ├── ai-service: StudentProfileAgent (LangGraph)
    │       │
    │       ├── Analyze academic performance (subject-wise)
    │       ├── Analyze attendance patterns
    │       ├── Analyze cognitive patterns (from AI tutor interactions)
    │       ├── Analyze vocabulary & language (from diary, assignments)
    │       └── Generate 360° profile JSON
    │
    ├── Save to MongoDB (ai_student_profiles)
    ├── Update Qdrant (student_profile_embeddings)
    │
    └── If anomaly detected:
            │
            ├── AlertAgent generates alert
            ├── Push to: Student (FCM) + Parent (FCM + WhatsApp) + Teacher (FCM)
            └── Save to analytics (dashboard)
```

---

## 3. Technology Stack (Final — Locked)

### Backend
| Component | Technology | Version |
|---|---|---|
| API Framework | FastAPI | 0.115.x |
| ASGI Server | Uvicorn + Gunicorn | Latest stable |
| Task Queue | Celery | 5.x |
| Task Scheduler | Celery Beat | 5.x |
| WebSocket | FastAPI WebSocket (native) | — |
| ORM | SQLAlchemy 2.0 (async) | 2.x |
| DB Migrations | Alembic | Latest |
| Mongo ODM | Motor (async) | 3.x |
| Validation | Pydantic v2 | 2.x |
| Auth | python-jose (JWT) | Latest |
| HTTP Client | httpx (async) | Latest |

### AI Layer
| Component | Technology |
|---|---|
| AI Orchestration | LangGraph |
| RAG Framework | LangChain |
| Embeddings | Google Gemini Embeddings / text-embedding-3-small |
| Vector Store | Qdrant (self-hosted Docker) |
| Primary LLM | Google Gemini 1.5 Pro (API) |
| Fallback LLM | Ollama (`gemma4:31b-cloud`) |
| Circuit Breaker | Tenacity (retry) + custom fallback |
| **AI Tool Standard** | **MCP (Model Context Protocol) — Phase 4.5** |
| **MCP SDK** | **mcp (Python SDK) + LangChain MCP Adapter** |
| **MCP Transport** | **Streamable HTTP (production) / stdio (dev)** |
| STT (Phase 2) | OpenAI Whisper |
| TTS (Phase 2) | **edge-tts** (Microsoft Edge TTS — 100% free, no API key) |
| Image Analysis (Phase 3) | Gemini Vision (Google AI Pro) |

### Frontend (Web)
| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State Management | Zustand |
| Data Fetching | TanStack Query (React Query) |
| Forms | React Hook Form + Zod |
| Charts | Recharts / Tremor |
| WebSocket | Native WebSocket API |
| Real-time Push | SSE (AI responses) + WebSocket (chat) |
| UI Components | shadcn/ui |

### Infrastructure

> **Pilot Strategy**: Azure Free Subscription + Google AI Pro. No AWS costs for pilot.
> **Scale Strategy**: Migrate to best-fit cloud (AWS/Azure/GCP) after revenue.

| Component | Dev | Test | Prod |
|---|---|---|---|
| Reverse Proxy | Nginx (local Docker) | Nginx (Azure VM) | Nginx (Azure Container Apps) |
| Containerization | Docker Compose | Docker Compose | Azure Container Apps / AKS |
| Container Registry | Local | Azure Container Registry (ACR) | Azure Container Registry (ACR) |
| Cloud | Local machine | Azure Free Subscription | Azure Free → Paid |
| LLM | Ollama (local) | Gemini API (Google AI Pro) | Gemini API (Google AI Pro) |
| PostgreSQL | Docker (local) | Azure DB for PostgreSQL Flexible Server | Azure DB for PostgreSQL Flexible Server |
| MongoDB | Docker (local) | MongoDB Atlas (M0 Free 512MB) | MongoDB Atlas (M2+ Paid) |
| Redis | Docker (local) | Docker on Azure VM | Azure Cache for Redis |
| File Storage | Local MinIO (Docker) | Azure Blob Storage | Azure Blob Storage |
| CDN | N/A | N/A | Azure CDN |
| SSL | Self-signed (local) | Let's Encrypt (Certbot) | Let's Encrypt / Azure App Gateway |
| CI/CD | Local scripts | GitHub Actions | GitHub Actions |
| Monitoring | Prometheus + Grafana (Docker) | Prometheus + Grafana (Docker) | Azure Monitor + Grafana |
| Logging | Console logs | Loki + Grafana (Docker) | Loki + Grafana / Azure Log Analytics |
| Secrets | .env files (local) | Azure Key Vault | Azure Key Vault |
| Ollama (LLM) | Local CPU/GPU | Azure VM (B2ms) | Azure VM (GPU) or Gemini API only |
| Ollama Model | `gemma4:31b-cloud` | `gemma4:31b-cloud` | Gemini API (no Ollama needed) |

### Third-Party Integrations
| Service | Provider | Phase |
|---|---|---|
| OTP / SMS | MSG91 | Phase 1 |
| Email | SendGrid | Phase 1 |
| Payments | Razorpay | Phase 5 |
| Push Notifications | Firebase Cloud Messaging (FCM) | Phase 3 |
| WhatsApp Notifications | MSG91 WhatsApp API / Meta Business | **Phase 6+ (deferred)** |

> [!NOTE]
> **WhatsApp deferred**: No WhatsApp Business account needed for pilot. SMS (MSG91) + FCM push covers all notification needs for Phase 1-5. WhatsApp will be added in Phase 6 when revenue justifies the Meta Business API subscription.

---

## 4. Security Architecture

### 4.1 Authentication Flow
```
1. User enters mobile number
2. Frontend → POST /auth/send-otp { mobile: "91XXXXXXXXXX" }
3. auth-service → MSG91 API → OTP sent
4. User enters OTP
5. Frontend → POST /auth/verify-otp { mobile, otp }
6. auth-service validates OTP (stored in Redis with 5min TTL)
7. If valid:
   - Issue JWT Access Token (15min expiry)
   - Issue Refresh Token (30 days, stored in Redis)
   - Return: { access_token, refresh_token, role, user_id }
8. Frontend stores tokens securely (HttpOnly cookies for web)
9. Every request: Authorization: Bearer <access_token>
10. auth-service middleware validates JWT on every protected route
```

### 4.2 RBAC Model
```
Roles (Enum):
  STUDENT          → Own data only
  PARENT           → Own children's data only
  TEACHER          → Assigned classes/subjects data
  CLASS_INCHARGE   → Full class data + escalation
  ADMIN            → Full school data
  OPERATIONS       → Module-specific (fee/transport/library)
  SUPER_ADMIN      → Multi-school (Phase 2 only)

Permission Matrix:
  Resource            STUDENT  PARENT  TEACHER  CLASS_IC  ADMIN
  ─────────────────────────────────────────────────────────────
  Own profile         R        R/W     R/W      R         R/W
  Child profile       -        R       -        -         R/W
  Student grades      R(own)   R(child)R/W      R         R/W
  Student attendance  R(own)   R(child)R/W      R         R/W
  Chat rooms          R/W(own) R/W     R/W      R         R
  AI tutor            R/W      R       -        -         R
  Fee details         R(own)   R/W     -        -         R/W
  Analytics           -        R(child)R(class) R(class)  R/W
  School config       -        -       -        -         R/W
```

### 4.3 Data Security
- All DB connections: SSL/TLS enforced
- PostgreSQL: Row-level security enabled (filtered by `school_id`)
- MongoDB: Field-level encryption for sensitive data
- S3: Private buckets, pre-signed URLs only (15min expiry)
- All API endpoints: Rate limiting via Nginx + Redis
- Secrets: Never in code — AWS Secrets Manager
- HTTPS only — HTTP redirected to HTTPS
- CORS: Strict whitelist of allowed origins
- SQL injection prevention: SQLAlchemy parameterized queries only
- Input validation: Pydantic v2 strict mode

---

## 5. Database Design (LLD)

### 5.1 PostgreSQL Schema

> **Critical Design Rule**: Every table carries `school_id UUID NOT NULL` for zero-migration multi-tenancy.

#### Core Tables

```sql
-- SCHOOLS (master table)
schools
  id              UUID PK
  name            VARCHAR(200) NOT NULL
  code            VARCHAR(20) UNIQUE NOT NULL
  address         JSONB
  settings        JSONB  -- (working_days, periods_per_day, etc.)
  subscription    JSONB  -- (plan, expiry — Phase 2)
  is_active       BOOLEAN DEFAULT TRUE
  created_at      TIMESTAMPTZ DEFAULT NOW()
  updated_at      TIMESTAMPTZ

-- USERS (central identity table)
users
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  mobile          VARCHAR(15) UNIQUE NOT NULL
  email           VARCHAR(255)
  full_name       VARCHAR(200) NOT NULL
  role            ENUM(student, parent, teacher, class_incharge, admin, operations)
  password_hash   VARCHAR(255)  -- optional (OTP primary)
  profile_photo   VARCHAR(500)  -- S3 URL
  is_active       BOOLEAN DEFAULT TRUE
  created_at      TIMESTAMPTZ DEFAULT NOW()
  updated_at      TIMESTAMPTZ
  INDEX: (school_id, role)
  INDEX: (mobile)

-- STUDENTS
students
  id              UUID PK
  user_id         UUID FK → users.id UNIQUE
  school_id       UUID FK → schools.id NOT NULL
  roll_no         VARCHAR(20)
  admission_no    VARCHAR(50) UNIQUE
  class_id        UUID FK → classes.id
  section_id      UUID FK → sections.id
  date_of_birth   DATE
  gender          ENUM(male, female, other)
  blood_group     VARCHAR(5)
  admission_date  DATE
  INDEX: (school_id, class_id)

-- PARENTS (one parent can have multiple children)
parents
  id              UUID PK
  user_id         UUID FK → users.id UNIQUE
  school_id       UUID FK → schools.id NOT NULL
  relationship    ENUM(father, mother, guardian)

-- STUDENT_PARENT_MAP
student_parent_map
  id              UUID PK
  student_id      UUID FK → students.id
  parent_id       UUID FK → parents.id
  is_primary      BOOLEAN DEFAULT FALSE
  UNIQUE: (student_id, parent_id)

-- TEACHERS
teachers
  id              UUID PK
  user_id         UUID FK → users.id UNIQUE
  school_id       UUID FK → schools.id NOT NULL
  employee_id     VARCHAR(50)
  qualification   TEXT
  joining_date    DATE
  department      VARCHAR(100)
  INDEX: (school_id)

-- CLASSES
classes
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  grade           VARCHAR(10)  -- "Grade 5", "Class 10"
  section         VARCHAR(5)   -- "A", "B"
  academic_year   VARCHAR(10)  -- "2024-25"
  class_incharge_id UUID FK → teachers.id
  UNIQUE: (school_id, grade, section, academic_year)

-- SUBJECTS
subjects
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  name            VARCHAR(100) NOT NULL
  code            VARCHAR(20)
  class_id        UUID FK → classes.id
  teacher_id      UUID FK → teachers.id
  INDEX: (school_id, class_id)

-- ATTENDANCE
attendance
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  student_id      UUID FK → students.id
  subject_id      UUID FK → subjects.id (NULL = overall daily attendance)
  date            DATE NOT NULL
  status          ENUM(present, absent, late, half_day)
  marked_by       UUID FK → users.id
  remarks         TEXT
  UNIQUE: (school_id, student_id, subject_id, date)
  INDEX: (school_id, student_id, date)
  INDEX: (school_id, date)

-- EXAMS
exams
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  class_id        UUID FK → classes.id
  subject_id      UUID FK → subjects.id
  exam_type       ENUM(unit_test, mid_term, final, assignment, quiz)
  title           VARCHAR(200)
  total_marks     DECIMAL(6,2)
  date            DATE
  created_by      UUID FK → users.id

-- GRADES (exam results)
grades
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  student_id      UUID FK → students.id
  exam_id         UUID FK → exams.id
  subject_id      UUID FK → subjects.id
  marks_obtained  DECIMAL(6,2)
  total_marks     DECIMAL(6,2)
  grade_letter    VARCHAR(5)   -- A+, A, B+...
  remarks         TEXT
  ai_feedback     TEXT         -- AI-generated feedback
  graded_by       UUID FK → users.id
  ai_graded       BOOLEAN DEFAULT FALSE
  INDEX: (school_id, student_id, subject_id)

-- ASSIGNMENTS
assignments
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  subject_id      UUID FK → subjects.id
  class_id        UUID FK → classes.id
  title           VARCHAR(200) NOT NULL
  description     TEXT
  file_url        VARCHAR(500)   -- S3 URL
  due_date        TIMESTAMPTZ
  created_by      UUID FK → users.id
  is_ai_generated BOOLEAN DEFAULT FALSE

-- ASSIGNMENT_SUBMISSIONS
assignment_submissions
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  assignment_id   UUID FK → assignments.id
  student_id      UUID FK → students.id
  file_url        VARCHAR(500)   -- S3 URL
  text_response   TEXT
  submitted_at    TIMESTAMPTZ DEFAULT NOW()
  marks_obtained  DECIMAL(6,2)
  feedback        TEXT
  ai_feedback     TEXT
  ai_graded       BOOLEAN DEFAULT FALSE
  status          ENUM(submitted, graded, late, missing)
  UNIQUE: (assignment_id, student_id)

-- TIMETABLE
timetable
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  class_id        UUID FK → classes.id
  subject_id      UUID FK → subjects.id
  teacher_id      UUID FK → teachers.id
  day_of_week     ENUM(monday, tuesday, wednesday, thursday, friday, saturday)
  period_number   INT
  start_time      TIME
  end_time        TIME
  UNIQUE: (school_id, class_id, day_of_week, period_number)

-- FEE_STRUCTURES
fee_structures
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  class_id        UUID FK → classes.id (NULL = all classes)
  fee_type        ENUM(tuition, transport, library, lab, sports, miscellaneous)
  amount          DECIMAL(10,2) NOT NULL
  due_day         INT            -- day of month
  frequency       ENUM(monthly, quarterly, annual, one_time)
  academic_year   VARCHAR(10)

-- FEES (student fee records)
fees
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  student_id      UUID FK → students.id
  fee_structure_id UUID FK → fee_structures.id
  amount          DECIMAL(10,2) NOT NULL
  due_date        DATE NOT NULL
  status          ENUM(pending, paid, overdue, waived, partial)
  paid_amount     DECIMAL(10,2) DEFAULT 0
  paid_at         TIMESTAMPTZ
  razorpay_order_id  VARCHAR(100)
  razorpay_payment_id VARCHAR(100)
  receipt_url     VARCHAR(500)  -- S3 URL
  INDEX: (school_id, student_id, status)
  INDEX: (school_id, due_date, status)

-- TRANSPORT_ROUTES
transport_routes
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  route_name      VARCHAR(100) NOT NULL
  vehicle_number  VARCHAR(20)
  driver_name     VARCHAR(100)
  driver_contact  VARCHAR(15)
  stops           JSONB  -- [{stop_name, lat, lng, time}]
  is_active       BOOLEAN DEFAULT TRUE

-- STUDENT_TRANSPORT
student_transport
  id              UUID PK
  student_id      UUID FK → students.id
  route_id        UUID FK → transport_routes.id
  boarding_stop   VARCHAR(100)

-- LIBRARY_BOOKS
library_books
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  title           VARCHAR(300) NOT NULL
  author          VARCHAR(200)
  isbn            VARCHAR(20)
  category        VARCHAR(100)
  total_copies    INT DEFAULT 1
  available_copies INT DEFAULT 1
  INDEX: (school_id, category)

-- LIBRARY_ISSUES
library_issues
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  book_id         UUID FK → library_books.id
  user_id         UUID FK → users.id
  issued_at       TIMESTAMPTZ DEFAULT NOW()
  due_date        DATE
  returned_at     TIMESTAMPTZ
  fine_amount     DECIMAL(8,2) DEFAULT 0
  status          ENUM(issued, returned, overdue)

-- EVENTS
events
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  title           VARCHAR(200) NOT NULL
  description     TEXT
  event_date      DATE
  event_time      TIME
  venue           VARCHAR(200)
  target_roles    JSONB  -- ['student', 'parent', 'teacher']
  created_by      UUID FK → users.id

-- NOTICES
notices
  id              UUID PK
  school_id       UUID FK → schools.id NOT NULL
  title           VARCHAR(200) NOT NULL
  content         TEXT
  target_roles    JSONB
  priority        ENUM(low, medium, high, urgent)
  is_ai_generated BOOLEAN DEFAULT FALSE
  created_by      UUID FK → users.id
  expires_at      TIMESTAMPTZ
  created_at      TIMESTAMPTZ DEFAULT NOW()
```

---

### 5.2 MongoDB Collections Design

```javascript
// CHAT_CONVERSATIONS
// One document per unique (student, parent, teacher, subject) combination
{
  _id: ObjectId,
  school_id: UUID,
  student_id: UUID,
  parent_id: UUID,
  teacher_id: UUID,
  subject_id: UUID,
  conversation_key: "student_uuid::parent_uuid::teacher_uuid::subject_uuid",  // unique index
  ai_fallback_enabled: Boolean,
  ai_fallback_delay_minutes: Number,  // default 15
  last_message_at: ISODate,
  teacher_last_responded_at: ISODate,
  created_at: ISODate,

  // Indexes: conversation_key (unique), school_id, student_id, teacher_id
}

// CHAT_MESSAGES
{
  _id: ObjectId,
  school_id: UUID,
  conversation_id: ObjectId,
  sender_id: UUID,
  sender_role: "student" | "parent" | "teacher" | "ai",
  message_type: "text" | "image" | "file" | "ai_response",
  content: String,
  file_url: String,
  ai_generated: Boolean,
  ai_model: String,  // "gemini-1.5-pro" | "llama-3.1"
  read_by: [{ user_id: UUID, read_at: ISODate }],
  is_escalated: Boolean,
  created_at: ISODate,

  // Indexes: (conversation_id, created_at), (school_id, created_at)
}

// AI_STUDENT_PROFILES
{
  _id: ObjectId,
  school_id: UUID,
  student_id: UUID,
  generated_at: ISODate,
  version: Number,
  academic: {
    subject_scores: [{ subject_id: UUID, name: String, avg_score: Number, trend: String }],
    overall_performance: String,  // "above_average" | "average" | "below_average"
    weak_subjects: [String],
    strong_subjects: [String],
    concept_application_gap: Boolean
  },
  cognitive: {
    learning_style: "visual" | "auditory" | "kinesthetic",
    problem_solving: String,
    logical_reasoning_score: Number,
    memory_type: "conceptual" | "rote"
  },
  language: {
    vocabulary_level: String,
    sentence_clarity: Number,
    reading_comprehension: Number,
    trend: String
  },
  behavioral: {
    consistency_score: Number,
    discipline_score: Number,
    improvement_rate: Number
  },
  attendance: {
    overall_percentage: Number,
    pattern: String,  // "regular" | "irregular" | "declining"
    risk_level: "low" | "medium" | "high"
  },
  ai_summary: String,  // Natural language summary
  ai_alerts: [{ type: String, message: String, severity: String, generated_at: ISODate }],
  recommendations: [{ type: String, content: String, resource_url: String }],

  // Indexes: (school_id, student_id) unique, generated_at
}

// AI_TUTOR_SESSIONS
{
  _id: ObjectId,
  school_id: UUID,
  student_id: UUID,
  subject_id: UUID,
  session_started: ISODate,
  session_ended: ISODate,
  messages: [
    {
      role: "student" | "ai",
      content: String,
      timestamp: ISODate,
      model_used: String,
      tokens_used: Number,
      rag_context_used: Boolean,
      weak_areas_addressed: [String]
    }
  ],
  topics_covered: [String],
  doubts_resolved: [String],
  follow_up_needed: [String],

  // Indexes: (school_id, student_id, session_started)
}

// STUDENT_DIARY
{
  _id: ObjectId,
  school_id: UUID,
  student_id: UUID,
  date: ISODate,
  tasks: [
    {
      id: UUID,
      type: "homework" | "exam_prep" | "revision" | "activity",
      subject_id: UUID,
      title: String,
      priority: "high" | "medium" | "low",
      estimated_time_mins: Number,
      completed: Boolean,
      completed_at: ISODate
    }
  ],
  ai_study_plan: {
    generated: Boolean,
    study_slots: [{ time: String, subject: String, activity: String, duration_mins: Number }],
    ai_note: String
  },
  mood: String,
  notes: String,

  // Indexes: (school_id, student_id, date) unique
}

// GAMIFICATION
{
  _id: ObjectId,
  school_id: UUID,
  student_id: UUID,
  total_xp: Number,
  level: Number,
  streak_days: Number,
  last_active: ISODate,
  badges: [{ id: String, name: String, earned_at: ISODate, description: String }],
  achievements: [{ type: String, value: Number, achieved_at: ISODate }],
  weekly_xp: Number,
  monthly_xp: Number,
  leaderboard_rank: Number,

  // Indexes: (school_id, student_id) unique, (school_id, total_xp)
}

// TEACHER_LESSON_PLANS
{
  _id: ObjectId,
  school_id: UUID,
  teacher_id: UUID,
  subject_id: UUID,
  class_id: UUID,
  week_number: Number,
  academic_year: String,
  content: {
    topics: [String],
    objectives: [String],
    activities: [String],
    resources: [String],
    assessment: String
  },
  ppt_url: String,  -- S3 URL
  ai_generated: Boolean,
  created_at: ISODate,

  // Indexes: (school_id, teacher_id, class_id, week_number)
}

// QUESTION_BANK
{
  _id: ObjectId,
  school_id: UUID,
  subject_id: UUID,
  class_id: UUID,
  topic: String,
  question_text: String,
  question_type: "mcq" | "short_answer" | "long_answer" | "fill_blank" | "true_false",
  difficulty: "easy" | "medium" | "hard",
  options: [String],  // for MCQ
  correct_answer: String,
  explanation: String,
  ai_generated: Boolean,
  bloom_level: String,  // remember, understand, apply, analyze, evaluate, create

  // Indexes: (school_id, subject_id, difficulty, question_type)
}

// NOTIFICATIONS_LOG
{
  _id: ObjectId,
  school_id: UUID,
  user_id: UUID,
  type: "push" | "sms" | "whatsapp" | "email",
  title: String,
  body: String,
  data: Object,
  status: "sent" | "failed" | "pending",
  sent_at: ISODate,
  read_at: ISODate,

  // Indexes: (school_id, user_id, sent_at)
}

// AUDIT_LOGS
{
  _id: ObjectId,
  school_id: UUID,
  actor_id: UUID,
  actor_role: String,
  action: String,  // "grade.update", "attendance.mark", "fee.pay", etc.
  resource_type: String,
  resource_id: String,
  before_state: Object,
  after_state: Object,
  ip_address: String,
  timestamp: ISODate,

  // Indexes: (school_id, timestamp), (school_id, actor_id), (resource_type, resource_id)
}
```

---

### 5.3 Qdrant Vector Collections

```
Collection: syllabus_content
  Vectors: 1536-dim (text embeddings of syllabus chapters, topics)
  Payload: { school_id, class_id, subject_id, topic, chapter, content_chunk, source }
  Use: RAG for AI Tutor (retrieve relevant syllabus context)

Collection: student_profiles
  Vectors: 1536-dim (embedding of student AI profile summary)
  Payload: { school_id, student_id, weak_areas, strong_areas, learning_style }
  Use: Personalize AI tutor explanations based on student profile

Collection: question_bank_vectors
  Vectors: 1536-dim (embedding of question text)
  Payload: { school_id, subject_id, difficulty, topic, question_id }
  Use: Semantic search for similar questions, anti-plagiarism
```

---

## 6. AI System Design (LLD)

### 6.1 LangGraph Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Orchestration Layer                    │
│                   (LangGraph State Machines)                 │
│                                                             │
│  ┌─────────────────┐   ┌──────────────────────────────────┐ │
│  │  TutorAgent     │   │    ChatFallbackAgent             │ │
│  │                 │   │                                  │ │
│  │ States:         │   │ States:                          │ │
│  │ → receive_query │   │ → monitor_chat                   │ │
│  │ → classify      │   │ → teacher_silent?                │ │
│  │ → rag_retrieve  │   │ → classify_message               │ │
│  │ → personalize   │   │ → generate_response / escalate   │ │
│  │ → generate      │   │ → notify_stakeholders            │ │
│  │ → validate      │   └──────────────────────────────────┘ │
│  │ → stream        │                                        │
│  └─────────────────┘   ┌──────────────────────────────────┐ │
│                        │    StudentProfileAgent            │ │
│  ┌─────────────────┐   │                                  │ │
│  │  AlertAgent     │   │ States:                          │ │
│  │                 │   │ → collect_data (pg + mongo)      │ │
│  │ States:         │   │ → analyze_academic               │ │
│  │ → detect_risk   │   │ → analyze_cognitive              │ │
│  │ → classify_risk │   │ → analyze_behavioral             │ │
│  │ → generate_msg  │   │ → synthesize_profile             │ │
│  │ → route_alert   │   │ → detect_alerts                  │ │
│  └─────────────────┘   └──────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────┐   ┌──────────────────────────────────┐ │
│  │ LessonPlanAgent │   │    GradingAgent                  │ │
│  │ StudyPlanAgent  │   │    QuestionPaperAgent            │ │
│  └─────────────────┘   └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 LLM Hybrid Strategy (Circuit Breaker)

```
Request comes in
    │
    ▼
Primary LLM: Gemini 1.5 Pro
    │
    ├── Success → Return response
    │
    └── Failure (timeout / rate limit / error)
              │
          Tenacity retry (max 2 attempts, 1s backoff)
              │
              └── Still failing?
                        │
                    Fallback to Ollama (gemma4:31b-cloud)
                        │
                        ├── Success → Return response + log fallback event
                        │
                        └── Failure → Return graceful degradation message
                                      + Alert admin (Slack/email)
                                      + Queue for retry later (Redis)

Cost Tracking per LLM call:
  - Store: { model, tokens_in, tokens_out, latency_ms, cost_usd, student_id, session_id }
  - Rate limit: Max 50 LLM calls/student/day (configurable per plan)
```

### 6.2.1 Semantic Response Cache (Cross-Student)

> **Key Design**: If Student 1 asks Q and gets response R, Student 2 asking a SIMILAR question gets the
> cached response instantly — zero LLM cost, sub-100ms response time.

```
New query arrives
    │
    ├── Step 1: Generate query embedding (Gemini Embeddings)
    │
    ├── Step 2: Exact cache hit? (Redis, key = hash(query + class_id + subject_id))
    │     HIT  ────────────────────────▶ Return immediately (< 5ms)
    │     MISS ─────────────────────────────────────────────────────┐
    │                                                               │
    ├── Step 3: Semantic cache hit? (Qdrant: cache_responses)       │
    │     Filter:  school_id + subject_id + class_id               │
    │     Threshold: cosine similarity > 0.92                      │
    │     HIT  ────────────────────────▶ Return cached (< 50ms)    │
    │           + Increment hit_count in Qdrant payload            │
    │     MISS ─────────────────────────────────────────────────────┘
    │
    ├── Step 4: Call LLM (Gemini → Ollama fallback)
    │
    └── Step 5: Store response in BOTH caches:
          Redis: key=hash(query+class+subject), TTL=1hr  (exact match, same student)
          Qdrant: cache_responses collection              (semantic match, all students)
                  Payload: { school_id, subject_id, class_id, query, response,
                             model_used, hit_count, created_at }

Cache Scenarios:
  Scenario A: Stud1 asks "What is photosynthesis?"
              → LLM responds → saved to cache
              Stud2 asks "Explain photosynthesis"
              → Semantic similarity 0.97 → Cache HIT → instant response

  Scenario B: Stud1 asks "Solve x² + 5x + 6 = 0"
              → LLM responds with steps → saved
              Stud2 asks "How to solve x² + 3x + 2 = 0"
              → Similarity < 0.92 (different coefficients) → Cache MISS → LLM called
              (Correct: different problem needs fresh solution)

  Scenario C: Teacher uploads new syllabus chapter
              → Invalidate cache for that subject_id in both Redis + Qdrant
              → Ensures responses reflect updated content

Security:
  - school_id ALWAYS filtered in Qdrant cache queries
  - No cross-school cache sharing
  - Cache keys never expose student_id (shared knowledge, not personal data)

New Qdrant Collection: cache_responses
  Vectors: 1536-dim (query embedding)
  Payload: { school_id, subject_id, class_id, query, response,
             model_used, hit_count, created_at, last_hit_at }
  TTL: Auto-expire entries not hit in 30 days
```

### 6.3 RAG Pipeline Design (AI Tutor)

```
Step 1: Ingest (Offline — admin uploads syllabus)
  PDF/Word Upload → file-service → S3
      │
  Celery Task: process_syllabus_document
      │
  PyPDF2 / python-docx → Extract text
      │
  RecursiveCharacterTextSplitter → chunks (512 tokens, 50 overlap)
      │
  Gemini Embeddings → 1536-dim vectors
      │
  Qdrant: Upsert to syllabus_content collection
  Metadata: { school_id, class_id, subject_id, topic, chunk_index }

Step 2: Query (Real-time — student asks question)
  Student query text
      │
  Gemini Embeddings → query vector
      │
  Qdrant: Similarity search (top-k=5, filter: school_id + class_id + subject_id)
      │
  Retrieved context chunks
      │
  Fetch student profile from MongoDB (weak areas, learning style)
      │
  Build personalized prompt:
    "You are a tutor for Class 7 students.
     Student learning style: visual
     Student weak areas: fractions, ratios
     Syllabus context: [chunks]
     Student question: [query]
     Provide a step-by-step explanation tailored to this student."
      │
  LLM generates response (streamed via SSE)
      │
  Save to ai_tutor_sessions (MongoDB)
      │
  Update weak_areas tracking in Redis cache
```

---

### 6.4 MCP Architecture Design (Phase 4.5)

> **When**: Introduced after AI Core (Phase 4) is stable. MCP wraps the existing service APIs as standardized tools.
> **Why**: Makes AI tools LLM-agnostic, modular, and accessible to any MCP-compatible client.

#### MCP Server Map

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP SERVER LAYER                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              school-data-mcp-server                     │   │
│  │  Wraps: academic-service + user-service APIs            │   │
│  │                                                         │   │
│  │  Tools:                                                 │   │
│  │    get_student_profile(student_id)                      │   │
│  │    get_student_grades(student_id, subject_id?, term?)   │   │
│  │    get_attendance_records(student_id, from?, to?)       │   │
│  │    get_class_students(class_id)                         │   │
│  │    get_subject_list(class_id)                           │   │
│  │    get_teacher_profile(teacher_id)                      │   │
│  │                                                         │   │
│  │  Resources:                                             │   │
│  │    student://{student_id}/profile                       │   │
│  │    student://{student_id}/grades                        │   │
│  │    class://{class_id}/performance                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              syllabus-mcp-server                        │   │
│  │  Wraps: Qdrant vector search + S3 syllabus content      │   │
│  │                                                         │   │
│  │  Tools:                                                 │   │
│  │    query_syllabus(query, subject_id, class_id)          │   │
│  │    get_syllabus_topics(subject_id, class_id)            │   │
│  │    search_concept(concept, difficulty?)                 │   │
│  │    get_chapter_content(chapter_id)                      │   │
│  │                                                         │   │
│  │  Resources:                                             │   │
│  │    syllabus://{subject_id}/{topic}                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              academic-mcp-server                        │   │
│  │  Wraps: academic-service (assignments, exams, questions) │   │
│  │                                                         │   │
│  │  Tools:                                                 │   │
│  │    get_assignments(class_id?, student_id?)              │   │
│  │    get_exam_schedule(class_id)                          │   │
│  │    get_question_bank(subject_id, difficulty?, topic?)   │   │
│  │    generate_questions(subject_id, topic, difficulty, n) │   │
│  │    search_similar_questions(question_text)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              analytics-mcp-server                       │   │
│  │  Wraps: analytics-service                               │   │
│  │                                                         │   │
│  │  Tools:                                                 │   │
│  │    get_student_risk_profile(student_id)                 │   │
│  │    get_class_performance_summary(class_id)              │   │
│  │    get_attendance_trend(student_id?, class_id?)         │   │
│  │    predict_academic_risk(student_id)                    │   │
│  │    get_fee_defaulter_risk(school_id)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              operations-mcp-server                      │   │
│  │  Wraps: school-ops-service                              │   │
│  │                                                         │   │
│  │  Tools:                                                 │   │
│  │    get_fee_status(student_id)                           │   │
│  │    get_transport_routes(school_id)                      │   │
│  │    get_library_availability(isbn?, title?)              │   │
│  │    get_upcoming_events(school_id, days?)                │   │
│  │    get_active_notices(school_id, role?)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼  Consumed by:
┌───────────────────────────────────────────────────────┐
│  LangGraph Agents (via LangChain MCP Adapter)         │
│  Claude Desktop (Teacher/Admin copilot)               │
│  Any MCP-compatible AI client (future integrations)   │
└───────────────────────────────────────────────────────┘
```

#### MCP Prompts (Pre-built Prompt Templates)

```
Prompt: analyze_student
  Arguments: student_id, focus_area (optional)
  Description: "Generate a comprehensive AI analysis for a student"
  Template: Automatically fetches profile + grades + attendance
              and structures the prompt for analysis

Prompt: generate_lesson_plan
  Arguments: subject_id, class_id, week_number, teacher_style
  Description: "Create a detailed weekly lesson plan from syllabus"

Prompt: create_question_paper
  Arguments: subject_id, class_id, difficulty_distribution, total_marks
  Description: "Generate a balanced question paper with bloom's levels"

Prompt: generate_parent_report
  Arguments: student_id, period (weekly/monthly)
  Description: "Create an AI-written parent progress report"
```

#### MCP Integration with LangGraph Agents

```python
# How LangGraph agents use MCP tools (via LangChain adapter)

# Before MCP (Phase 4 — custom tools, tightly coupled):
@tool
def get_student_grades(student_id: str) -> dict:
    """Custom HTTP call to academic-service"""
    return httpx.get(f"/v1/academic/grades/{student_id}").json()

# After MCP (Phase 4.5 — standardized, LLM-agnostic):
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient({
    "school-data": {"url": "http://school-data-mcp:8001/mcp", "transport": "streamable_http"},
    "syllabus":    {"url": "http://syllabus-mcp:8002/mcp",    "transport": "streamable_http"},
    "analytics":   {"url": "http://analytics-mcp:8003/mcp",   "transport": "streamable_http"},
})

# LangGraph agent automatically uses MCP tools
tools = await mcp_client.get_tools()  # Discovers all tools from all servers
agent = create_react_agent(llm=gemini, tools=tools)
```

#### MCP Security Model

```
Each MCP server enforces:
  - school_id scoping on ALL tool calls (no cross-school data leakage)
  - JWT validation on MCP endpoint (same auth-service token)
  - Role-based tool access:
      Teachers     → school-data, syllabus, academic MCP tools
      Admins       → All MCP tools
      AI Agents    → All MCP tools (internal service account JWT)
      Claude Desk. → Scoped to requesting teacher's role permissions
  - Audit log: Every MCP tool call logged to MongoDB (audit_logs)
  - Rate limiting: 100 MCP calls/user/minute via Nginx
```

#### MCP Project Structure

```
services/
├── mcp-servers/
│   ├── school-data-mcp/       # FastAPI MCP server
│   │   ├── server.py          # MCP tool definitions
│   │   ├── tools/             # Tool implementations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── syllabus-mcp/
│   ├── academic-mcp/
│   ├── analytics-mcp/
│   └── operations-mcp/        #   Fee/transport/library tools
```

### 6.5 Self-Improving Agent System Design (AGENT.md)

> **Core Philosophy**: The AI system gets better every day without manual intervention.
> It learns from every interaction, improves accuracy over time, and adapts to each student, teacher, and school.

#### 6.5.1 Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT MEMORY SYSTEM                          │
│                                                                 │
│  ┌───────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Short-Term Memory │  │ Long-Term Memory │  │Semantic Mem  │ │
│  │                   │  │                 │  │              │ │
│  │  Redis            │  │  MongoDB        │  │  Qdrant      │ │
│  │  - Conv context   │  │  - Student hist │  │  - Knowledge │ │
│  │  - Session state  │  │  - Interactions │  │  - Embeddings│ │
│  │  TTL: 1 hour      │  │  - Patterns     │  │  - Cache     │ │
│  └───────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.5.2 Self-Improvement Loop

```
User Interaction
    │
    ▼
Agent generates Response
    │
    ▼
Feedback Collection (Explicit + Implicit)
    │
    ├── Explicit: User ratings (👍/👎), corrections, teacher overrides
    └── Implicit: Follow-up questions, time spent, re-asks, usage patterns
    │
    ▼
Quality Evaluation Engine
    │
    ├── Track: accuracy, hallucination rate, resolution rate
    ├── Compare: prompt versions (A/B), model versions
    └── Score: response quality (0-100)
    │
    ▼
Learning Update (Celery task: nightly)
    │
    ├── Prompt Optimization: prefer prompt variants with higher scores
    ├── Retrieval Improvement: re-rank chunks based on which ones led to ✅ responses
    ├── Weakness Detection: flag topics with high follow-up rate → needs better RAG
    └── Profile Update: update student weak areas based on follow-up patterns
    │
    ▼
Improved Future Response
```

#### 6.5.3 Feedback Storage Schema (MongoDB)

```javascript
// AGENT_FEEDBACK
{
  _id: ObjectId,
  school_id: UUID,
  session_id: ObjectId,           // ai_tutor_sessions._id
  message_index: Number,          // which message in session
  agent_type: "tutor" | "chat_fallback" | "study_plan" | "alert",
  prompt_version: String,         // "tutor_v1.2.0"
  response_quality_score: Number, // 0-100 (auto-computed)

  // Explicit feedback
  user_rating: Number,            // 1-5 (null if not given)
  user_correction: String,        // if student corrected the AI
  teacher_override: Boolean,      // teacher corrected AI response

  // Implicit signals
  follow_up_count: Number,        // How many follow-ups after this response
  time_to_next_message_ms: Number,// Low = student understood quickly
  session_resolved: Boolean,      // Did student stop asking after this?

  // RAG tracking
  rag_chunks_used: [String],      // chunk IDs that were retrieved
  rag_helpful: Boolean,           // did RAG improve response?

  // Outcome
  improvement_applied: Boolean,   // was this used in a learning update?
  created_at: ISODate
}

// PROMPT_VERSIONS
{
  _id: ObjectId,
  agent_type: String,
  version: String,                // "tutor_v1.2.0"
  prompt_template: String,
  avg_quality_score: Number,
  response_count: Number,
  resolution_rate: Number,
  is_active: Boolean,
  created_at: ISODate
}
```

#### 6.5.4 Agent Evaluation Framework

```
Metrics tracked per agent (daily Celery task):

┌─────────────────┬──────────────────────────────────────────────┐
│ Metric          │ How Measured                                 │
├─────────────────┼──────────────────────────────────────────────┤
│ Resolution Rate │ Sessions where follow-up count = 0           │
│ Satisfaction    │ Average user_rating (if given)               │
│ Accuracy        │ Teacher override rate (lower = better)       │
│ Hallucination   │ Responses flagged with correction            │
│ Response Speed  │ Avg latency_ms per agent call                │
│ Cache Hit Rate  │ % responses served from semantic cache       │
│ LLM Cost        │ Daily cost_usd per school per agent          │
└─────────────────┴──────────────────────────────────────────────┘

Thresholds (trigger alert to admin):
  Resolution Rate < 70%     → RAG improvement needed
  Hallucination Rate > 5%   → Guardrail tightening needed
  Teacher Override > 10%    → Prompt retuning needed
  LLM Cost > budget/day     → Rate limiting adjustment needed
```

#### 6.5.5 Guardrails

```
Agent must:
  ✅ If confidence < threshold → Ask clarifying question instead of guessing
  ✅ If academic scope unclear → "This seems outside your syllabus. Let me check."
  ✅ If personal/sensitive content → Escalate to teacher immediately
  ✅ If repeated wrong answers → Flag to teacher + stop AI responses for that topic
  ✅ Never expose data across school boundaries (school_id enforced)
  ✅ Never fabricate references, page numbers, or book names
```

#### 6.5.6 Agent Versioning & Rollback

```
Each agent has:
  - agent_type: "tutor" | "chat_fallback" | "profiler" | "study_plan" etc.
  - prompt_version: Semantic versioning (v1.0.0, v1.1.0...)
  - model_version: Gemini 1.5 Pro, Gemini 2.0, Llama 3.1 8B...

A/B Testing:
  20% traffic → new prompt version
  80% traffic → current stable version
  After 7 days: compare metrics → promote or rollback

Rollback:
  PROMPT_VERSIONS.is_active = false → immediate rollback
  All agents read active prompt version from cache (Redis) at startup
```

#### 6.5.7 Observability Pipeline

```
Every agent decision logged:
  - Agent type + version
  - Input (query + context summary)
  - Retrieved RAG chunks (IDs)
  - LLM called (model + tokens)
  - Response quality score
  - Feedback received

Tools:
  - Structured JSON logs → Azure Monitor/Log Analytics
  - LangSmith (optional) for LangGraph tracing
  - Custom dashboard in analytics-service (admin can view agent performance)
```

---

## 7. Communication System Design (LLD)

### 7.1 Chat Room Architecture

```
Chat Room Key = f"{student_id}::{parent_id}::{teacher_id}::{subject_id}"
  → Unique room per (student, parent, subject teacher) triplet
  → Student in 5 subjects → 5 separate rooms (one per subject teacher)
  → Parent sees all their child's rooms

WebSocket Connection Management:
  User connects → WS /ws/chat/{room_id}?token=JWT
  auth-service validates JWT in WS handshake
  connection registered in Redis: ws_connections:{user_id} = {room_ids: [], connection_id}
  Redis Pub/Sub channel per room: chat_room:{room_id}

Message Flow:
  Sender → WS Server (communication-service)
      │
  Validate sender belongs to room
      │
  Save message to MongoDB (chat_messages)
      │
  Publish to Redis channel: chat_room:{room_id}
      │
  All subscribers (online users in room) receive via WS
      │
  For offline users → FCM push notification
```

### 7.2 AI Fallback - Detailed State Machine

```
States: IDLE → MONITORING → AI_RESPONDING → ESCALATED → RESOLVED

Trigger: Student or Parent sends message
  │
  START monitoring (Celery delayed task, delay = fallback_delay_minutes)
  │
  Teacher sends response within delay?
    YES → Cancel Celery task → State: RESOLVED
    NO  →
          1. Fetch message (MongoDB)
          2. Classify via LLM:
             - "academic_doubt" | "homework" | "general" | "complaint" | "emergency"
          │
          academic_doubt or homework?
            YES →
                  Fetch student profile + RAG context
                  Generate personalized AI response
                  Send as AI message (role: "ai") in chat
                  FCM notify student/parent: "AI tutor has responded"
                  FCM remind teacher: "Pending message, AI responded"
                  State: AI_RESPONDING
            NO  →
                  Send: "Your message has been noted. Teacher will respond soon."
                  Escalate to class_incharge (FCM + DB record)
                  State: ESCALATED
          │
          After additional delay (30min), teacher still silent?
            Escalate to Admin (FCM + Dashboard alert)
            Log response_time_breach in analytics
```

---

## 8. API Design Principles

### 8.1 URL Conventions
```
Base URL: https://api.school.com/v1/

Format: /v1/{service}/{resource}/{id}/{sub-resource}
Examples:
  GET    /v1/academic/students/{id}/grades
  GET    /v1/academic/students/{id}/attendance
  POST   /v1/academic/assignments
  GET    /v1/ai/tutor/sessions/{student_id}
  POST   /v1/ai/tutor/ask
  GET    /v1/chat/rooms/{room_id}/messages
  WS     /v1/ws/chat/{room_id}
  POST   /v1/auth/send-otp
  GET    /v1/analytics/students/{id}/profile
```

### 8.2 Standard Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  },
  "timestamp": "2024-01-20T10:30:00Z"
}

// Error format:
{
  "success": false,
  "error": {
    "code": "GRADE_NOT_FOUND",
    "message": "Grade record not found",
    "details": {}
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 8.3 Pagination, Filtering, Sorting
```
?page=1&per_page=20
?sort=created_at:desc
?filter[status]=pending
?filter[class_id]=uuid
?search=student_name
```

---

## 9. Celery Task System Design

```
Task Categories:

CRITICAL (max_retries=5, retry_backoff=True):
  - send_otp_sms
  - razorpay_webhook_process
  - chat_ai_fallback_check

HIGH (max_retries=3):
  - push_notification_send
  - whatsapp_message_send
  - fee_reminder_send

MEDIUM (max_retries=3):
  - student_profile_generate
  - report_generate
  - alert_generate

LOW (max_retries=1):
  - leaderboard_update
  - analytics_aggregate
  - syllabus_document_process

Celery Beat Schedules:
  Every day   06:00 AM → generate_daily_study_plans (all students)
  Every day   09:00 PM → run_student_profile_analysis (all students)
  Every week  Sunday  → generate_weekly_reports (all students)
  Every day           → check_overdue_fees → send_reminders
  Every hour          → update_leaderboard_rankings
  Every 15min         → check_pending_chat_messages (AI fallback)
```

---

## 10. Notification System Design

```
NotificationService (communication-service)

Channels:
1. FCM (Firebase) → Mobile push notifications
   - Priority: HIGH for urgent alerts, NORMAL for regular updates
   - Topic subscriptions: school_{id}, class_{id}, role_{name}

2. MSG91 SMS → OTP + Critical alerts (payment, attendance, emergency)
   - OTP: 6-digit, 5 min expiry, max 3 attempts

3. WhatsApp Business API → Parent notifications (highest open rate in India)
   - Templates: fee_reminder, attendance_alert, performance_report, ai_insight
   - Requires Meta-approved templates

4. SendGrid Email → Formal: report cards, fee receipts, admin communications

Notification Routing Logic:
  URGENT (risk alert, emergency)  → FCM + SMS + WhatsApp (all 3)
  HIGH (fee overdue, AI alert)    → FCM + WhatsApp
  MEDIUM (homework, new notice)   → FCM only
  LOW (gamification milestone)    → FCM only

User Preferences:
  Users can configure channel preferences in profile settings
  Stored in PostgreSQL (users.notification_preferences JSONB)
```

---

## 11. File Management Design

```
Strategy: Client-side direct upload to S3 via pre-signed URLs
(Backend never handles file bytes — only generates signed URLs)

Flow:
1. Client → POST /v1/files/upload-url { file_name, file_type, context }
2. file-service validates: allowed types, max size (context-based)
3. file-service → AWS S3 → generate pre-signed PUT URL (15 min expiry)
4. file-service → Save metadata to PostgreSQL (files table)
5. Return: { upload_url, file_id, public_view_url }
6. Client → PUT directly to S3 (no backend involved)
7. Client → POST /v1/files/confirm-upload { file_id }
8. file-service marks file as uploaded

Bucket Structure:
  s3://school-platform-files/
    ├── {school_id}/assignments/{file}
    ├── {school_id}/submissions/{file}
    ├── {school_id}/syllabus/{file}
    ├── {school_id}/lesson-plans/{file}
    ├── {school_id}/question-papers/{file}
    ├── {school_id}/profile-photos/{file}
    └── {school_id}/receipts/{file}

CloudFront Distribution:
  - For read-heavy assets (profile photos, question papers)
  - Signed cookies for authenticated assets
  - Cache-Control: max-age=31536000 for static assets
```

---

## 12. Monorepo Project Structure

```
school-management-platform/
│
├── 📁 services/                    # All backend microservices
│   ├── auth-service/               # FastAPI: Auth, JWT, OTP
│   │   ├── app/
│   │   │   ├── api/v1/            # Route handlers
│   │   │   ├── core/              # Config, security, deps
│   │   │   ├── models/            # SQLAlchemy models
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── services/          # Business logic
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── alembic/               # DB migrations
│   │
│   ├── user-service/
│   ├── academic-service/
│   ├── communication-service/
│   ├── ai-service/
│   ├── school-ops-service/
│   ├── analytics-service/
│   ├── file-service/
│   └── mcp-servers/               # MCP Tool Servers (Phase 4.5)
│       ├── school-data-mcp/       #   Student/grade/attendance tools
│       ├── syllabus-mcp/          #   RAG + Qdrant query tools
│       ├── academic-mcp/          #   Assignments/exam/question tools
│       ├── analytics-mcp/         #   Risk/dashboard/report tools
│       └── operations-mcp/        #   Fee/transport/library tools
│
├── 📁 frontend/                    # Next.js web application
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── (admin)/           # Admin route group
│   │   │   ├── (teacher)/         # Teacher route group
│   │   │   ├── (student)/         # Student route group
│   │   │   ├── (parent)/          # Parent route group
│   │   │   ├── auth/              # Login pages
│   │   │   └── layout.tsx
│   │   ├── components/            # Shared UI components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── lib/                   # API clients, utils
│   │   ├── store/                 # Zustand state stores
│   │   └── types/                 # TypeScript types
│   ├── package.json
│   └── Dockerfile
│
├── 📁 mobile/                      # Flutter app (Phase 2)
│
├── 📁 shared/                      # Shared across services
│   ├── schemas/                   # Shared Pydantic schemas
│   ├── constants/                 # Error codes, enums
│   ├── utils/                     # Common utilities
│   └── proto/                     # Protobuf (if needed later)
│
├── 📁 infra/                            # Infrastructure as Code
│   ├── docker/
│   │   ├── docker-compose.dev.yml       # 🔵 DEV: Full local stack
│   │   ├── docker-compose.test.yml      # 🟡 TEST: Azure VM deployment
│   │   ├── docker-compose.prod.yml      # 🟢 PROD: Azure Container Apps
│   │   └── nginx/
│   │       ├── nginx.dev.conf
│   │       ├── nginx.test.conf
│   │       └── nginx.prod.conf
│   ├── environments/
│   │   ├── .env.dev                     # Dev vars (local services)
│   │   ├── .env.test                    # Test vars (Azure free tier)
│   │   └── .env.prod.example            # Prod template (real secrets → Azure Key Vault)
│   ├── azure/                           # Azure IaC (Bicep)
│   │   ├── rg-school-ms-dev.bicep       # school-management-system-dev
│   │   ├── rg-school-ms-test.bicep      # school-management-system-test
│   │   └── rg-school-ms-prod.bicep      # school-management-system-prod
│   └── k8s/                             # AKS manifests (Phase 2 Prod)
│
├── 📁 data/                        # Project documentation
│   └── SMS_Features.txt
│
├── 📁 docs/                        # Technical documentation
│   ├── api/                       # API specs (OpenAPI)
│   ├── architecture/              # Architecture diagrams
│   └── runbooks/                  # Operational runbooks
│
├── 📁 scripts/                     # Dev/ops scripts
│   ├── setup.sh
│   ├── seed_db.py
│   └── generate_schemas.py
│
├── .github/
│   └── workflows/
│       ├── ci.yml                 # CI pipeline
│       └── deploy.yml             # CD pipeline
│
├── .env.example                   # Environment variables template
└── README.md
```

---

## 13. Development Phases & Roadmap

### Phase 1 — Foundation (Weeks 1-4)
```
✦ Project scaffolding (monorepo structure)
✦ Docker Compose setup (all infra: PG, Mongo, Redis, Qdrant, Ollama)
✦ auth-service: OTP login, JWT, RBAC middleware
✦ user-service: User profiles, onboarding flows
✦ Next.js setup: Role-based routing, auth pages, design system
✦ Database migrations (Alembic)
✦ CI pipeline setup (GitHub Actions)
```

### Phase 2 — Academic Core (Weeks 5-8)
```
✦ academic-service: Students, Classes, Subjects, Attendance, Grades
✦ Timetable management
✦ Assignment management
✦ Teacher dashboard (web)
✦ Student dashboard (web)
✦ Parent dashboard (web)
```

### Phase 3 — Communication System (Weeks 9-11)
```
✦ communication-service: Structured chat rooms
✦ WebSocket real-time chat
✦ AI fallback mechanism (Celery tasks)
✦ Escalation workflows
✦ Notification service (FCM, SMS, WhatsApp)
```

### Phase 4 — AI Core (Weeks 12-16)
```
✦ ai-service: LangGraph agents
✦ RAG pipeline (syllabus ingestion + query)
✦ AI Tutor (Phase 1: Text-based)
✦ Student Profile Agent (360° profiling)
✦ Alert Agent (risk detection)
✦ Study Plan Agent
✦ Lesson Plan Agent
```

### Phase 5 — School Operations (Weeks 17-20)
```
✦ school-ops-service: Fee management (Razorpay)
✦ Transport management
✦ Library management
✦ Events & Notices
✦ Analytics dashboards
✦ Gamification engine
```

### Phase 4.5 — MCP Integration (Weeks 16-17, overlaps Phase 5)
```
✦ Build 5 MCP servers (school-data, syllabus, academic, analytics, operations)
✦ Migrate LangGraph agent tools to use LangChain MCP Adapter
✦ Enable Claude Desktop / admin AI copilot access via MCP
✦ MCP security: school_id scoping + JWT + audit logs
✦ MCP tool testing: validate all tools with normal + edge cases
```

### Phase 6 — Advanced AI (Weeks 21-24)
```
✦ Auto question paper generation (via QuestionPaperAgent + academic-mcp)
✦ AI grading (subjective) (via GradingAgent)
✦ Teacher lesson plan generation + PPT (via LessonPlanAgent + syllabus-mcp)
✦ Predictive analytics (academic risk, fee default) (via analytics-mcp)
✦ AI Tutor Phase 2: Voice (Whisper + TTS)
```

### Phase 7 — Flutter Mobile (Weeks 25-30)
```
✦ Student mobile app
✦ Parent mobile app
✦ Teacher mobile app
```

### Phase 8 — Production Hardening (Weeks 31-32)
```
✦ K8s migration (AWS EKS)
✦ Performance testing
✦ Security audit
✦ Multi-tenancy preparation
```

---

## 14. 🔍 Self-Review: Scalability & Design Flaws Analysis

> _"Reviewed as a Principal Engineer. The following issues were identified and resolved in this design."_

### Issue 1: WebSocket Horizontal Scaling ⚠️
**Problem**: If we run multiple `communication-service` instances, a user connected to Instance A won't receive messages published to Instance B.
**Resolution**: Redis Pub/Sub used as the message broker between WS instances. Each instance subscribes to the same Redis channel for a room. This allows horizontal scaling of WebSocket servers.

### Issue 2: School-ID Missing = Multi-Tenancy Disaster ⚠️
**Problem**: Starting single-school and adding `school_id` later requires a full schema migration.
**Resolution**: `school_id UUID NOT NULL` present on EVERY table from Day 1. PostgreSQL Row-Level Security enabled by default. Zero migration effort when scaling to SaaS.

### Issue 3: AI Service as Single Point of Failure ⚠️
**Problem**: All AI operations route through one `ai-service`. If it goes down, all AI features break.
**Resolution**: 
  - Celery async tasks decouple AI from request-response cycle.
  - Circuit breaker (Tenacity) + Ollama fallback.
  - AI tutor uses SSE streaming — if LLM fails mid-stream, graceful error message injected.
  - Non-critical AI tasks (profiling, plan generation) are queued, not blocking.

### Issue 4: S3 Upload via Backend = Bandwidth Bottleneck ⚠️
**Problem**: If backend receives file uploads, heavy files (PPTs, videos) will saturate service bandwidth.
**Resolution**: Pre-signed URL strategy — client uploads directly to S3. Backend only generates signed URLs and confirms completion.

### Issue 5: Kafka Over-Engineering for Phase 1 ⚠️
**Problem**: Kafka has high operational complexity (Zookeeper, cluster management) — overkill for a single school.
**Resolution**: Redis Streams + Celery for Phase 1. Architecture designed so Kafka can replace Redis Streams in Phase 2 with minimal service changes.

### Issue 6: JWT Logout / Token Invalidation ⚠️
**Problem**: JWT tokens are stateless — logging out doesn't invalidate them.
**Resolution**: Maintain a `token_blacklist` in Redis (key=jti, TTL=token_expiry). Middleware checks blacklist on every request. Refresh tokens stored in Redis with full revocation support.

### Issue 7: LLM Cost Control ⚠️
**Problem**: Unlimited LLM calls per student can make the platform financially unviable.
**Resolution**: 
  - Per-student daily LLM call limit (configurable, default 50 calls/day)
  - Tracked in Redis counter: `llm_calls:{student_id}:{date}`
  - AI response caching for identical queries (Redis, 1hr TTL)
  - Token usage logged to MongoDB for billing/analytics

### Issue 8: Celery Task Idempotency ⚠️
**Problem**: Celery tasks can be retried. Double-processing (e.g., fee webhooks, OTP sends) causes bugs.
**Resolution**: Each task carries an `idempotency_key`. Redis SET NX used to enforce exactly-once processing. Webhook events stored with `event_id` and deduplicated.

### Issue 9: MongoDB Index Strategy ⚠️
**Problem**: Unindexed MongoDB collections will cause full collection scans as data grows.
**Resolution**: All collections have compound indexes defined upfront (see Collection Design). TTL indexes on session logs (90-day auto-expiry). Covered indexes for most query patterns.

### Issue 10: Razorpay Webhook Security ⚠️
**Problem**: Unvalidated webhooks can fake payment success.
**Resolution**: HMAC-SHA256 signature validation on every webhook. `razorpay_payment_id` cross-verified with Razorpay API before updating fee status. Idempotency key on webhook processing.

### Issue 11: Regional Language Support Gap ⚠️
**Problem**: India has many regional languages. String-only design breaks multilingual support.
**Resolution**: 
  - All text fields: UTF-8 (PostgreSQL + MongoDB default, confirmed) 
  - LLM prompts include language instruction (detect from user profile)
  - i18n support in Next.js from Day 1 (next-intl)
  - AI Tutor can respond in student's preferred language

### Issue 12: No Rate Limiting on OTP Endpoint ⚠️
**Problem**: OTP endpoint can be abused for SMS bombing.
**Resolution**: 
  - Max 3 OTP requests per mobile per hour (Redis counter)
  - 5-minute cooldown between OTP sends
  - IP-based rate limiting via Nginx
  - CAPTCHA on frontend after 2nd attempt

### Issue 13: MCP Tool Sprawl & School-ID Leakage ⚠️
**Problem**: MCP tools exposed to Claude Desktop or external agents could accidentally leak data across schools if `school_id` is not enforced at the MCP layer (not just the service layer).
**Resolution**:
  - Every MCP tool has `school_id` as a **mandatory, server-side injected** parameter — it is NEVER passed by the AI client, always extracted from the JWT token in the MCP request header.
  - MCP server middleware validates JWT → extracts school_id → scopes all DB queries automatically.
  - MCP tool definitions marked with role permissions — LangGraph internal agents get broader access, teacher/admin copilot gets role-scoped access only.
  - All MCP tool calls logged to MongoDB `audit_logs` with actor_id, school_id, tool_name, arguments, and timestamp.
  - MCP tool count reviewed each phase — if > 30 tools per server, decompose into sub-servers to prevent tool confusion in LLM context.

---

## 15. Open Questions — ✅ All Resolved

> [!IMPORTANT]
> All questions answered. Architecture is fully locked. Ready to scaffold.

| # | Question | Answer | Impact |
|---|---|---|---|
| 1 | Academic Year | **April–March** | Timetable, attendance reset, report generation calendar locked |
| 2 | Grading System | **Configurable** | Admin-defined: marks (0-100) + grade letter (A+/A/B+...), set per school |
| 3 | AI Fallback Timer | **15 minutes** (queries) / 60 min (complaints) | Celery task delay values locked |
| 4 | WhatsApp Business | **Deferred to Phase 6+** | SMS (MSG91) + FCM covers pilot. No Meta Business API needed now |
| 5 | Ollama Hosting | **Azure VM (B2ms)** or **Google AI Pro (Gemini API)** | No separate GPU server needed for Phase 1 — Gemini API primary |
| 6 | First Module | **Academic Core** (attendance + grades) after auth + user | Phase 2 plan confirmed |
| 7 | UI Theme | **Krediy ERP style** → [Figma Link](https://www.figma.com/community/file/1536325311178740562/krediy-erp) | Clean, professional ERP aesthetic — light theme, card-based dashboards |

---

## 16. Verification Plan

### Architecture Validation
- [ ] Each service boundary reviewed for single-responsibility
- [ ] Database schema reviewed for normalization + index coverage
- [ ] AI agent workflows reviewed for error paths
- [ ] Security model validated (RBAC matrix complete)
- [ ] Scalability reviewed (WebSocket, DB, AI — all addressed)

### Post-Scaffold Validation (Phase 1)
- Docker Compose: All services start without error
- Auth: OTP send + verify + JWT issue + refresh + logout cycle
- RBAC: Each role blocked from unauthorized endpoints (automated tests)
- DB: All migrations run cleanly, indexes created

---

---

## 16. Environment Architecture Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│                    THREE-ENVIRONMENT STRATEGY                        │
├─────────────────┬────────────────────────┬────────────────────────── │
│  🔵 DEV         │  🟡 TEST               │  🟢 PROD                 │
│  school-ms-dev  │  school-ms-test        │  school-ms-prod           │
├─────────────────┼────────────────────────┼────────────────────────── │
│  Local machine  │  Azure Free (VM)       │  Azure Container Apps     │
│  Docker Compose │  Docker Compose        │  AKS / ACA                │
│  .env.dev       │  .env.test             │  Azure Key Vault          │
│  Ollama local   │  Gemini API (free)     │  Gemini API (Pro)         │
│  gemma4:31b     │  (no Ollama in test)   │  (no Ollama in prod)      │
│  MinIO (S3-like)│  Azure Blob (free)     │  Azure Blob               │
│  PG in Docker   │  Azure PG (free tier)  │  Azure PG (Flex Server)   │
│  Mongo Docker   │  Atlas M0 (free)       │  Atlas M2+ (paid)         │
│  Redis Docker   │  Redis Docker on VM    │  Azure Cache for Redis    │
│  No CDN         │  No CDN                │  Azure CDN                │
│  self-signed    │  Let's Encrypt         │  Let's Encrypt / AGWY     │
└─────────────────┴────────────────────────┴───────────────────────────┘

Naming Convention (Azure Resource Groups):
  school-management-system-dev
  school-management-system-test
  school-management-system-prod

CI/CD Pipeline (GitHub Actions):
  Push to dev branch    → Deploy to school-management-system-dev
  Push to test branch   → Deploy to school-management-system-test
  Push to main branch   → Deploy to school-management-system-prod (manual approval)
```

---

*Architecture Version 1.2 — Fully Locked — Awaiting Final Approval to Begin Scaffolding*
