# StudyNexs — Platform Architecture

> **How the system is organized internally** — product layers, AI platform, and request paths.
> **Where software runs:** [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md).
> **What each hostname means:** [`URL_ARCHITECTURE.md`](./URL_ARCHITECTURE.md).
> **Engineering policy:** [`/CLAUDE.md`](../CLAUDE.md).

**Owner:** Avinash Reddy Masapeta · **Status:** v1.0 draft · **Last updated:** 2026-07-16  
> Freeze after Gate 1A — see [`DEPLOYMENT_CONVENTIONS.md`](./DEPLOYMENT_CONVENTIONS.md) §12.

---

## 1. Three diagrams — three questions

StudyNexs maintains **three architecture views**. Do not merge them into one diagram.

| Diagram | Document | Answers |
|---------|----------|---------|
| **Deployment Architecture** | [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) | Where does the software run? |
| **Platform Architecture** | This file | How is the system organized internally? |
| **Request Flow** | This file §3 | How does a user's request travel through the system? |

Update the diagram that matches the change you are making. Cross-link when a concept spans views.

---

## 2. Platform Architecture (conceptual)

This is the **Noustriks / StudyNexs product stack** — not infrastructure. It shows why StudyNexs is
not a generic multi-tenant CRUD app.

```mermaid
flowchart TB
    subgraph Noustriks["Noustriks (product owner)"]
        SN[StudyNexs Platform]
    end

    subgraph Identity["Request identity"]
        TR[Tenant Resolver<br/>subdomain / X-Tenant-Slug]
        AUTH[Authentication + RBAC<br/>JWT school_id]
    end

    subgraph DNA["Company DNA (tenant context)"]
        SC[School Config<br/>board, locale, branding]
        CP[CurriculumPack<br/>approved academic source]
        KG[Knowledge Graph<br/>concepts, links]
    end

    subgraph Core["FastAPI modular monolith"]
        OPS[School Operations<br/>fees, attendance, exams, …]
        API[Domain services<br/>school_id scoped]
    end

    subgraph AIPlatform["Shared AI Platform"]
        GW[AI Gateway<br/>provider-agnostic]
        RAG[RAG Engine<br/>retrieve + cite]
        EMB[Embeddings]
        CR[Credits + metering]
    end

    subgraph Intelligence["Intelligence pillars"]
        CI[Curriculum Intelligence]
        AI[Assessment Intelligence]
        LI[Learning Intelligence]
        SOI[School Operations Intelligence]
    end

    subgraph Copilots["Copilots (human-in-the-loop)"]
        TC[Teacher Copilot]
        PC[Parent Copilot]
        STC[Student Copilot]
    end

    subgraph Providers["LLM providers (env-configured)"]
        GEM[Gemini]
        OAI[OpenAI]
        CLA[Claude / Anthropic]
        FUT[Future providers]
    end

    subgraph Vector["Retrieval store"]
        QD[(Qdrant)]
    end

    SN --> TR
    TR --> AUTH
    AUTH --> SC
    SC --> CP
    CP --> KG
    KG --> API

    API --> OPS
    API --> Intelligence
    Intelligence --> AIPlatform

    GW --> GEM
    GW --> OAI
    GW --> CLA
    GW --> FUT

    RAG --> EMB
    RAG --> QD
    EMB --> OAI

    AIPlatform --> Copilots
    CR -.-> GW
```

### 2.1 What “Company DNA” means here

**Company DNA** is the tenant-specific academic and operational context that makes AI outputs
**school-grounded**, not generic:

| Layer | Implementation (today) | Role |
|-------|------------------------|------|
| School config | `School` row — board, slug, settings | Who this tenant is |
| CurriculumPack | `app/modules/curriculum` — versioned packs | What we teach (content is data) |
| Knowledge Graph | Concepts, links, ConceptCards | Structured curriculum + mastery spine |
| Tenant scope | `school_id` on every row + vector filter | Isolation |

Generic SaaS stops at tenant ID. StudyNexs adds **approved curriculum** as the grounding layer
for papers, evaluation, copilots, and tutor content.

### 2.2 AI Gateway vs direct provider calls

**No domain code calls Gemini/OpenAI directly.** All LLM traffic goes through
`app/modules/ai/gateway` — provider selection, timeouts, metering, and safe error mapping live
there. Diagrams must show **FastAPI → AI Gateway → providers**, not FastAPI → Gemini.

### 2.3 RAG vs Qdrant

**Qdrant is storage.** **RAG Engine** (`app/modules/ai/rag`) owns chunking, embedding, retrieval,
re-ranking, and citation formatting. Flow: **FastAPI → RAG Engine → Embeddings → Qdrant**.

---

## 3. Request Flow — teacher generates a question paper

End-to-end path for a representative AI workflow (Assessment Intelligence).

```mermaid
sequenceDiagram
    actor T as Teacher
    participant FE as dps.studynexs.com<br/>(Cloudflare Pages)
    participant CF as Cloudflare<br/>DNS / WAF / CDN / SSL
    participant NGX as Nginx / API Gateway
    participant TR as Tenant Resolver
    participant AUTH as Auth + JWT
    participant API as FastAPI
    participant DNA as School + CurriculumPack
    participant GW as AI Gateway
    participant RAG as RAG Engine
    participant LLM as Gemini / OpenAI / …
    participant PG as PostgreSQL

    T->>FE: Open AI Papers, click Generate
    FE->>FE: getTenantSlug() → "dps"
    FE->>CF: HTTPS API call
    CF->>NGX: api.studynexs.com
    Note over NGX: Rate limit, TLS, proxy headers
    NGX->>TR: Forward request
    Note over TR: Host=api (reserved)<br/>X-Tenant-Slug: dps
    TR->>AUTH: Validate Bearer + school_id match
    AUTH->>DNA: Load pack / class context
    DNA->>RAG: Grounding context (optional)
    RAG->>API: Cited curriculum slice
    API->>GW: LLM request (metered)
    GW->>LLM: Provider call
    LLM-->>GW: Draft JSON
    GW-->>API: Normalized response
    API->>PG: Persist draft (HITL)
    API-->>FE: Paper draft + citations
    FE-->>T: Review / approve
```

### 3.1 Request flow checklist

| Step | Component | Failure mode |
|------|-----------|--------------|
| 1 | Frontend tenant slug | Wrong school if hostname/env misconfigured |
| 2 | Cloudflare | WAF block, cache miss |
| 3 | Nginx | Rate limit 429 |
| 4 | Tenant resolver | 400 if no slug on platform API host |
| 5 | JWT + tenant match | 401 / 403 cross-tenant |
| 6 | Company DNA / pack | 400 ungrounded generation refused |
| 7 | AI Gateway | 503 provider down → fallback (Gate 1B) |
| 8 | HITL | Teacher approves before publish |

---

## 4. Background processing (async path)

Long-running work (eval jobs, notifications, future analytics) uses **Redis-backed queues**, not
synchronous HTTP.

```mermaid
flowchart LR
    API[FastAPI] -->|enqueue| RQ[Redis Queue<br/>Arq / outbox]
    RQ --> W[Background Worker]
    W --> LLM[AI Gateway → LLM]
    W --> PG[(PostgreSQL)]
    W --> OBJ[(Object Storage<br/>reports, sheets)]
    W --> NOTIFY[SMS / email / push<br/>future]
```

| Redis role | Uses today |
|------------|------------|
| Cache | User session cache (60s TTL) |
| Sessions / auth | OTP, refresh JTIs, token blacklist |
| Rate limits | Per user + school |
| Background jobs | Arq + embedded outbox worker |

**Today:** outbox worker runs **inside** the API process. **Scale-out:** separate worker container
(same Redis + Postgres + AI Gateway).

---

## 5. Storage (logical)

Object storage is **provider-agnostic** in diagrams (OCI, Azure, S3-compatible).

| Bucket purpose | Examples |
|----------------|----------|
| Student uploads | Profile docs, admission files |
| Answer sheets | Exam scan uploads |
| Generated reports | PDF report cards, export papers |
| Backups | DB dumps, config snapshots (off-VM) |

**Today:** local disk (`/app/uploads`) — acceptable for demo/pilot only.

---

## 6. Monitoring (platform view)

Observability spans **edge and origin**:

```mermaid
flowchart TB
    CF[Cloudflare<br/>analytics, WAF events] --> MON[Monitoring]
    NGX[Nginx access logs] --> MON
    API[FastAPI structlog] --> MON
    OTEL[OpenTelemetry] --> MON
    MON --> LOG[Logs]
    MON --> MET[Metrics<br/>Prometheus]
    MON --> TRACE[Traces<br/>Tempo]
    MET --> GRAF[Grafana dashboards]
    LOG --> ALERT[Alerts]
    MET --> ALERT
```

Scaffold: `infra/observability/` (Prometheus, Grafana, Tempo, OTEL collector). Production cutover
is Gate 2+.

---

## 7. Maturity note

This diagram set is **v1.0 draft** — intentionally not frozen until after Gate 1A deploy validates
the paths. Revise when:

- Object storage replaces local disk
- Workers split from API
- Company DNA gains explicit provisioning APIs
- New intelligence pillars ship (Batch 30+)

---

## 8. Related documents

| Document | Scope |
|----------|-------|
| [`DEPLOYMENT_ARCHITECTURE.md`](./DEPLOYMENT_ARCHITECTURE.md) | Cloud, Docker, env, deploy flow |
| [`URL_ARCHITECTURE.md`](./URL_ARCHITECTURE.md) | Hostnames, reserved subdomains |
| [`PRODUCT.md`](./PRODUCT.md) | Product vision, four pillars |
| [`PLATFORM_STATUS.md`](./PLATFORM_STATUS.md) | Live engineering state |
