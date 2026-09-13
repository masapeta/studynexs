# StudyNexs — Product Design, Agentic Architecture & Frontend Redesign Documentation Pack

> **Document Status:** Authoritative Product & Architectural Specification  
> **Target Version:** StudyNexs 2.0 (Agentic Academic Operating System)  
> **Owner:** Avinash Reddy Masapeta (ARM) / Noustriks  
> **Charter Alignment:** `AGENTS.md` / `CLAUDE.md` §14, §17, §33, §42, §53, §97, §106

---

## Table of Contents
1. [Executive Product Design Vision](#1-executive-product-design-vision)
2. [Brand Application Rules Based on Final Logo](#2-brand-application-rules-based-on-final-logo)
3. [Chat-First Workspace UX](#3-chat-first-workspace-ux)
4. [Shortcut Action Widget System](#4-shortcut-action-widget-system)
5. [Visual Design System](#5-visual-design-system)
6. [UX Principles](#6-ux-principles)
7. [Information Architecture](#7-information-architecture)
8. [Role-Based Navigation](#8-role-based-navigation)
9. [Agentic Interaction Model](#9-agentic-interaction-model)
10. [Backend Orchestration Model](#10-backend-orchestration-model)
11. [Structured Response Block Contract](#11-structured-response-block-contract)
12. [Core Screen Specifications](#12-core-screen-specifications)
13. [Component System](#13-component-system)
14. [Workflow Panel Patterns](#14-workflow-panel-patterns)
15. [Trust, Governance, Audit, and Human-in-the-Loop UX](#15-trust-governance-audit-and-human-in-the-loop-ux)
16. [Responsive Design Rules](#16-responsive-design-rules)
17. [Accessibility Checklist](#17-accessibility-checklist)
18. [Frontend Implementation Plan](#18-frontend-implementation-plan)
19. [Backend Contract Requirements](#19-backend-contract-requirements)
20. [Phase-by-Phase Delivery Plan](#20-phase-by-phase-delivery-plan)

---

## 1. Executive Product Design Vision

### 1.1 The Shift: From Menu-Driven ERP to Agentic Command Workspace
Traditional education software acts merely as a **passive record silo**—a cluttered collection of menus, disjointed forms, tables, and static charts. Users spend significant cognitive energy searching for records, cross-referencing tabs, and calculating eligibility manually.

**StudyNexs 2.0 transforms this model entirely:**
StudyNexs is an **AI-First Academic Command Center** powered by a strictly governed agentic interaction layer. The first screen after login is a **chat-first command surface** that anchors the entire institution around an intuitive **Ask → Verify → Act** paradigm.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             STUDYNEXS 2.0 PARADIGM                          │
├───────────────────────┬────────────────────────────┬────────────────────────┤
│          ASK          │           VERIFY           │          ACT           │
│ Natural language      │ Typed, deterministic       │ Contextual workflow    │
│ intent input or       │ institutional checks &     │ panels, approval       │
│ 1-click shortcut      │ domain service records     │ chains, and human      │
│ widgets               │ with clear citations       │ confirmation gates     │
└───────────────────────┴────────────────────────────┴────────────────────────┘
```

### 1.2 Product Principle: AI Explains, Deterministic Systems Decide
* **The AI Layer:** Understands natural language intent, extracts parameters, plans tool execution, drafts explanations, and guides workflows.
* **The System Layer:** Authoritative domain services, database constraints, institutional policy engines, role-based access controls, and audit trails calculate official attendance, determine eligibility, compute grades, and mutate records.
* **Non-Negotiable Rule:** AI never invents grades, never calculates attendance on its own, never silently executes mutations, and never bypasses institutional review.

---

## 2. Brand Application Rules Based on Final Logo

### 2.1 Brand Anchors
* **Brand Name:** `StudyNexs` (Exact casing; always capitalized S and N).
* **Owner/Parent:** Noustriks.
* **Product Feel:** Institutional, calm, authoritative, modern, focused, trustworthy. Never childish; no cartoon avatars, noisy gradients, or decorative clutter.

### 2.2 Palette Specifications
The palette derives directly from the finalized StudyNexs brand assets:

| Token Name | Hex / RGB | Usage Context |
|---|---|---|
| `--sn-brand-primary` | `#0B132B` / `rgb(11, 19, 43)` | Deep Midnight Navy: Topbars, active borders, primary headings |
| `--sn-brand-indigo` | `#1C2541` / `rgb(28, 37, 65)` | Slate Navy: Cards, neutral structural containers |
| `--sn-brand-accent` | `#0066FF` / `rgb(0, 102, 255)` | Electric Academic Blue: Primary action buttons, active focus rings, key status chips |
| `--sn-brand-cyan` | `#00F5D4` / `rgb(0, 245, 212)` | Bright Cyan Accent: Verified status indicators, positive progress badges |
| `--sn-surface-bg` | `#080D1A` / `rgb(8, 13, 26)` | Dark glass ambient background |
| `--sn-surface-card` | `rgba(18, 26, 47, 0.72)` | Translucent layered glass card fill |
| `--sn-surface-border` | `rgba(255, 255, 255, 0.08)` | Crisp structural line borders |
| `--sn-text-primary` | `#F8FAFC` | Main headings, primary labels |
| `--sn-text-secondary` | `#94A3B8` | Body descriptions, metadata |
| `--sn-text-muted` | `#64748B` | Timestamps, micro-labels |

### 2.3 Typography
* **Primary Sans:** `Inter` or `Manrope` (CSS font-family: `var(--font-sans)`).
* **Header / Editorial:** Clean geometric weights (`font-semibold` to `font-bold` for metric cards; `tabular-nums` for all quantitative figures).

---

## 3. Chat-First Workspace UX

### 3.1 The Three-Zone Master Workspace

```
┌──────────┬──────────────────────────────────────────────┬───────────────────────────┐
│ 1. SLIM  │ 2. CENTER COMMAND WORKSPACE                  │ 3. RIGHT WORKFLOW PANEL   │
│ SIDEBAR  ├──────────────────────────────────────────────┤ (Dynamic Context Slide-in)│
│ (Icons)  │ Sticky Topbar: Context + Role + Status Pills │                           │
│          ├──────────────────────────────────────────────┤ ┌───────────────────────┐ │
│ ⊞ Home   │ Welcome: "How can StudyNexs help your day?"  │ │ ACTIVE WORKFLOW       │ │
│ 💬 Chat  │                                              │ │ Step 1: Policy Check  │ │
│ 🎓 Acad  │ ┌──────────────────────────────────────────┐ │ │ Step 2: Verification  │ │
│ 📋 Tasks │ │ Shortcut Action Widgets (Grid of 6)      │ │ │ Step 3: Approval      │ │
│ 🕘 Hist  │ └──────────────────────────────────────────┘ │ ├───────────────────────┤ │
│ ⚙ Config │ ┌──────────────────────────────────────────┐ │ │ Blockers / Citations  │ │
│          │ │ Conversation Stream: Structured Cards    │ │ │ [Action: Confirm]     │ │
│          │ └──────────────────────────────────────────┘ │ └───────────────────────┘ │
│          │ [ 💬 Ask StudyNexs anything...          ⏎ ] │                           │
└──────────┴──────────────────────────────────────────────┴───────────────────────────┘
```

1. **Left Navigation (Slim Icon Rail, 64px width):**
   * Home / Dashboard Command Center (`⊞`)
   * New Chat / Turn (`💬`)
   * My Academics / Records (`🎓`)
   * Tasks / Approval Queues (`📋`)
   * Session History (`🕘`)
   * Settings & Tenant Config (`⚙`)

2. **Center Command Workspace (Primary Focus, flex-1):**
   * **Header Banner:** Welcome greeting with current institutional term context.
   * **Shortcut Action Grid:** 4–8 role-specific instant action tiles.
   * **Chat Conversation Stream:** Structured response blocks, prompt chips, and verified result cards.
   * **Bottom Fixed Composer:** Persistent input with file attachment, mic input, and send actions.

3. **Right Context & Workflow Panel (Collapsible 380px–460px Slide-Over):**
   * Triggered when a turn requires multi-step action, approval, or deep inspection.
   * Shows step progression, validation errors, policy clauses, and confirmation buttons.

### 3.2 Sticky Topbar Specifications
* **Left:** Active Workspace Title / Conversation Subject (`Class 10A Mathematics Mastery`).
* **Center:** System Status Pills (Live connection status: `LMS ●`, `SIS ●`, `Exams ●`, `Fees ●`).
* **Right:** 
  * Active Role Badge (`Principal`, `Faculty`, `Student`, `Parent`).
  * Role Switcher dropdown (Development / Demo mode).
  * Notification Bell with unread counter.
  * User avatar and profile trigger.

---

## 4. Shortcut Action Widget System

### 4.1 Shortcut Interaction Law
A shortcut widget is **not a decorative link**. Clicking a shortcut triggers an immediate deterministic intent pipeline:
1. Focuses and populates the chat stream.
2. Triggers the backend agentic orchestrator or deterministic route immediately.
3. Renders the structured verification payload directly into the center stream.
4. Opens the right-side workflow panel if action or confirmation is required.

### 4.2 Role-Pivoted Shortcut Catalog

#### A. Student Shortcuts
| Widget Label | Triggered Intent | Target Backend Tool / Service | Right Panel Action |
|---|---|---|---|
| **Check Attendance** | `"Check my current attendance and shortage warnings"` | `GetStudentAttendanceSummary` | None (Direct Result Card) |
| **Today's Timetable** | `"Show my schedule and class venues for today"` | `GetStudentTimetable` | Class Room Navigator |
| **Pending Assignments** | `"Show my pending homework and submission deadlines"` | `GetPendingAssignments` | Submission Drawer |
| **Exam Eligibility** | `"Am I eligible for upcoming semester examinations?"` | `CheckExamEligibility` | Exception Appeal Form |
| **Fee Status** | `"Check pending fee dues and receipt history"` | `GetStudentFeeStatus` | Pay Now / Receipt PDF |
| **Apply for Leave** | `"I want to apply for medical/personal leave"` | `StartLeaveWorkflow` | Multi-step Leave Form |
| **Request Certificate** | `"Generate a bonafide / study certificate request"` | `StartCertificateRequest` | Request Confirmation |
| **Weak Subject Remedial** | `"Show my weakest topics and practice recommendations"` | `GetStudentWeakConcepts` | Study Plan Generator |

#### B. Faculty / Teacher Shortcuts
| Widget Label | Triggered Intent | Target Backend Tool / Service | Right Panel Action |
|---|---|---|---|
| **At-Risk Students** | `"Show students below 75% attendance or declining marks"` | `GetClassRiskProfile` | Intervention Planner |
| **Pending Leave Approvals** | `"List student leave requests waiting for my approval"` | `ListTeacherPendingApprovals` | 1-Click Approval Queue |
| **Assignment Review Queue** | `"Show submissions pending grading and rubrics"` | `GetAssignmentReviewQueue` | Quick-Grader Modal |
| **Weak Concept Report** | `"Which topics in Chapter 4 had the highest error rate?"` | `GetClassWeakConcepts` | Remedial Resource Pack |
| **Exam Eligibility Queue** | `"Show students with attendance condonation flags"` | `GetHallTicketEligibilityQueue`| Exemption Review |
| **Class Attendance Snapshot**| `"Take or review today's attendance for Class 10A"` | `GetTodayAttendanceSheet` | Quick Submit Sheet |

#### C. Admin / Principal Shortcuts
| Widget Label | Triggered Intent | Target Backend Tool / Service | Right Panel Action |
|---|---|---|---|
| **Hall Ticket Readiness** | `"Show institution-wide exam fee and attendance clearance"`| `GetExamClearanceStatus` | Batch Publish Gate |
| **Certificate Approvals** | `"Show pending bonafide and transfer certificate requests"`| `ListPendingCertificates` | Sign & Seal Drawer |
| **Fee Hold Exceptions** | `"List students with fee-hold registration blocks"` | `ListFeeHoldOverrides` | Temporary Override |
| **Staff Attendance Overview**| `"Show staff on leave and substitution gaps today"` | `GetStaffDailyOverview` | Substitution Allocator |

---

## 5. Visual Design System

### 5.1 Design Tokens (CSS Custom Properties)

```css
:root {
  /* Surface Tokens */
  --sn-bg-root: #080D1A;
  --sn-bg-surface-elevated: rgba(18, 26, 47, 0.75);
  --sn-bg-surface-glass: rgba(255, 255, 255, 0.03);
  --sn-bg-surface-hover: rgba(255, 255, 255, 0.06);
  --sn-bg-bubble-user: rgba(0, 102, 255, 0.12);
  --sn-bg-bubble-ai: #0E172A;

  /* Line & Border Tokens */
  --sn-border-subtle: rgba(255, 255, 255, 0.08);
  --sn-border-focus: #0066FF;
  --sn-border-verified: #00F5D4;

  /* Semantic Feedback Tokens */
  --sn-color-success: #10B981;
  --sn-color-warning: #F59E0B;
  --sn-color-danger: #EF4444;
  --sn-color-info: #0066FF;

  /* Radius Ladder */
  --sn-radius-sm: 6px;
  --sn-radius-md: 10px;
  --sn-radius-lg: 16px;
  --sn-radius-xl: 24px;
  --sn-radius-full: 9999px;

  /* Spacing Scale */
  --sn-space-1: 4px;
  --sn-space-2: 8px;
  --sn-space-3: 12px;
  --sn-space-4: 16px;
  --sn-space-6: 24px;
  --sn-space-8: 32px;

  /* Shadow Elevation */
  --sn-shadow-card: 0 4px 20px rgba(0, 0, 0, 0.25);
  --sn-shadow-drawer: -8px 0 32px rgba(0, 0, 0, 0.40);
  --sn-shadow-glow-accent: 0 0 16px rgba(0, 102, 255, 0.25);
}
```

---

## 6. UX Principles (The 6 Command Laws)

1. **Ask → Verify → Act:** Everything begins with user intent, proves truth with verified records, and resolves in clean, human-governed actions.
2. **Deterministic Data, Generative Explanations:** Real numbers and statuses are query results from domain databases; LLMs synthesize clarity and next steps, never data.
3. **No Dead Ends:** Every response card must provide at least one relevant follow-up chip or workflow launch trigger.
4. **Human-in-the-Loop for Consequence:** Financial payments, grade submissions, leave approvals, and student risk flags require explicit human clicks.
5. **Calm, High-Information Density:** Glass surfaces, crisp micro-typography, and structured badge indicators minimize clutter while maximizing institutional context.
6. **Instant Feedback:** Optimistic UI state transitions with clear skeleton loaders on all async steps.

---

## 7. Information Architecture

```
StudyNexs Platform Architecture
├── Workspace Shell (AppShell.tsx)
│   ├── Topbar (Topbar.tsx)
│   │   ├── Title + Subject Context
│   │   ├── Live System Status Cluster
│   │   └── Role / Persona Switcher
│   ├── Slim Sidebar (SidebarRail.tsx)
│   ├── Main Command Center (CenterWorkspace.tsx)
│   │   ├── Welcome Hero (WelcomeHero.tsx)
│   │   ├── Shortcut Widget Grid (ShortcutGrid.tsx)
│   │   ├── Chat Stream (ChatThread.tsx)
│   │   │   ├── User Message Bubble (UserBubble.tsx)
│   │   │   └── AI Structured Response (AiResponseCard.tsx)
│   │   │       ├── Text Explanation Block
│   │   │       ├── Verified Result Card
│   │   │       ├── Source Citation Strip
│   │   │       └── Next-Step Action Buttons
│   │   └── Chat Composer (ChatInput.tsx)
│   └── Right Workflow Panel (WorkflowDrawer.tsx)
│       ├── Workflow Stepper (Stepper.tsx)
│       ├── Rule Verification Accordion
│       ├── Approval Chain Preview
│       └── Final Confirmation Footer
```

---

## 8. Role-Based Navigation & Access Boundaries

| Role | Topbar Scope | Permitted Tool Namespaces | Default Shortcut Tiles |
|---|---|---|---|
| **Student** | Own Profile, Section, Major | `student:*`, `academics:read_own`, `attendance:read_own` | Timetable, Attendance, Assignments, Fee Status |
| **Faculty / Teacher** | Assigned Classes & Subjects | `teacher:*`, `mastery:*`, `eval:review`, `leave:approve` | At-Risk Students, Leave Approvals, Quick Attendance |
| **Academic Coordinator / HOD** | Department Scope | `curriculum:*`, `approvals:*`, `moderation:*` | Curriculum Packs, Staff Absence, Exam Readiness |
| **Admin / Principal** | Institution-Wide (Tenant) | `admin:*`, `finance:*`, `ops:*`, `compliance:*` | Hall Tickets, Fee Exceptions, Staff Allocation |
| **Parent / Guardian** | Linked Student(s) Only | `parent:*`, `fees:pay`, `attendance:view_child` | Child Attendance, Fee Dues, Report Card, Teacher Note |

---

## 9. Agentic Interaction Model

### 9.1 Intent Classification Pipeline

```
User Query: "Why is Aarav ineligible for the semester exam?"
                      │
                      ▼
        [1. Intent & Scope Classification]
        • Entity: Student (Aarav, Class 10A)
        • Target: Exam Eligibility Rules
        • Actor: Subject Teacher (Scope: Class 10A Maths)
                      │
                      ▼
         [2. Deterministic Tool Execution]
        ├── Call: CheckExamEligibility(student_id, exam_id)
        │   ├── Attendance: 71.4% (Threshold: 75.0%) -> ❌ SHORTAGE
        │   ├── Internal Marks: 22/30 (Threshold: 15/30) -> ✅ PASS
        │   └── Fee Status: Dues cleared -> ✅ CLEAR
        └── Call: GetAttendanceBreakdown(student_id)
                      │
                      ▼
        [3. Structured Payload Assembly]
        • Block 1: verified_result_card (Status: Ineligible)
        • Block 2: blocker_list (Shortage: 3.6% / 4 classes needed)
        • Block 3: source_citation_strip (Attendance System, Exam Rule §4.2)
        • Block 4: action_list ("Apply for Medical Condonation", "View Details")
                      │
                      ▼
        [4. LLM Summary & Presentation]
        Synthesizes human explanation grounded ONLY in Block 1–4 facts.
```

---

## 10. Backend Orchestration Model

The backend is built around **5 strict layers**:

```
Layer 1: FastAPI Route & Session Gateway (/api/v1/workspace/turn)
                 │
                 ▼
Layer 2: Agentic Orchestrator (Intent Resolver & Tool Dispatcher)
                 │
                 ▼
Layer 3: Governed Tool Registry (Role, Tenant Scope, & Input Sanitizer)
                 │
                 ▼
Layer 4: Deterministic Domain Services (Attendance, Exams, Fees, Mastery)
                 │
                 ▼
Layer 5: Presentation Assembler (Typed UI Block Packager)
```

---

## 11. Structured Response Block Contract

Every response from `/api/v1/workspace/turn` conforms to the strict `WorkspaceResponse` JSON schema:

```json
{
  "request_id": "9f8b4c3e-...",
  "correlation_id": "turn-1049-...",
  "message": {
    "title": "Exam Eligibility Check: Aarav Reddy",
    "summary": "Aarav is currently ineligible for Semester 1 Exams due to an attendance shortage in Mathematics (71.4% vs 75.0% required).",
    "tone": "cautious"
  },
  "blocks": [
    {
      "type": "student_card",
      "priority": "primary",
      "payload": {
        "student_id": "std-4091",
        "display_name": "Aarav Reddy",
        "class_label": "Class 10",
        "section_label": "Section A",
        "admission_no": "24017"
      }
    },
    {
      "type": "metric_row",
      "priority": "primary",
      "payload": {
        "items": [
          { "label": "Attendance", "value": "71.4%", "status": "risk" },
          { "label": "Threshold", "value": "75.0%", "status": "normal" },
          { "label": "Classes Needed", "value": "4 Periods", "status": "warning" },
          { "label": "Fee Status", "value": "Cleared", "status": "normal" }
        ]
      }
    },
    {
      "type": "blocker_list",
      "priority": "primary",
      "payload": {
        "blockers": [
          {
            "code": "ATTENDANCE_SHORTAGE",
            "title": "Attendance Shortage in Mathematics",
            "description": "Student has attended 50/70 sessions (71.4%). Requires minimum 75% under Academic Board Rule §4.2."
          }
        ]
      }
    },
    {
      "type": "citation_list",
      "priority": "secondary",
      "payload": {
        "items": [
          {
            "label": "Attendance Records (Live)",
            "source_type": "database",
            "source_id": "attendance_logs_2026",
            "summary": "Verified as of 10-Sep-2026 09:30 AM IST"
          },
          {
            "label": "Institutional Examination Regulation 2026",
            "source_type": "policy",
            "source_id": "sec-4-clause-2",
            "summary": "Mandatory 75% physical attendance per subject"
          }
        ]
      }
    }
  ],
  "actions": [
    {
      "label": "Initiate Medical Condonation Workflow",
      "action_type": "workflow_launch",
      "href": "/dashboard/teaching/condonation?studentId=std-4091",
      "permission_gate": "can_manage_attendance_exceptions",
      "enabled": true
    },
    {
      "label": "View Full Assessment History",
      "action_type": "navigate",
      "href": "/dashboard/students/std-4091",
      "permission_gate": "can_view_students",
      "enabled": true
    }
  ],
  "verification": {
    "status": "verified",
    "checked_at": "2026-09-13T10:45:00Z",
    "source_systems": ["SIS_POSTGRES", "EXAM_REGISTRY"]
  },
  "telemetry": {
    "used_model": "deterministic_router",
    "used_fallback": false,
    "tool_calls": 2,
    "tool_failures": 0
  }
}
```

---

## 12. Core Screen Specifications

### 12.1 Screen 1: The Unified Home Command Workspace
* **Header:** Sticky glass navigation with role context and system heartbeat.
* **Hero Banner:** "How can StudyNexs help your academic day?" with instant search/query bar.
* **Shortcut Deck:** 2-column on mobile, 4-column on desktop bento grid of action triggers.
* **Active Stream:** Dynamic chat thread showcasing prompt interactions and result cards.
* **Bottom Bar:** Fixed input composer with multiline expansion and audio prompt trigger.

### 12.2 Screen 2: Faculty Mastery & Intervention Studio
* **Trigger:** `"Show weak concepts for Class 10A Science"`
* **Output:** Inline mastery breakdown card + misconception cluster + 1-click button: `"Draft 10-Minute Remedial Sheet"`.
* **Workflow Drawer:** Slides in with lesson objectives, generated questions, and printable PDF preview.

### 12.3 Screen 3: Student Self-Service & Exam Clearance
* **Trigger:** `"Am I eligible for exams?"`
* **Output:** Hall ticket clearance breakdown tile (Fees, Attendance, Labs, Library).
* **Direct Action:** Digital Hall Ticket download button or Condonation request button.

---

## 13. Component System

The frontend architecture consists of **24 core reusable primitives**:

1. `AppShell.tsx` — Responsive 3-zone layout orchestrator.
2. `SidebarRail.tsx` — 64px slim navigation with active icon states.
3. `Topbar.tsx` — Sticky breadcrumb, live system health, and role badge.
4. `WelcomeHero.tsx` — Greeting banner and prompt trigger zone.
5. `ShortcutGrid.tsx` — Grid container for role-based action widgets.
6. `ShortcutCard.tsx` — Interactive glass tile with icon, title, and intent hook.
7. `ChatThread.tsx` — Virtualized message container with scroll anchoring.
8. `UserBubble.tsx` — Right-aligned user turn with avatar and timestamp.
9. `AiResponseCard.tsx` — Master card housing structured response blocks.
10. `StudentCardWidget.tsx` — Verified student profile header with admission metadata.
11. `MetricRowWidget.tsx` — KPI tiles with status color indicators (Normal, Warning, Risk).
12. `DataTableWidget.tsx` — Sortable, paginated verified records table.
13. `BlockerListWidget.tsx` — Red-tinted alert accordion detailing rule violations.
14. `CitationStripWidget.tsx` — Micro-badges linking to verified data systems.
15. `ActionButtonsWidget.tsx` — Primary and secondary workflow launch triggers.
16. `WorkflowDrawer.tsx` — Right-hand contextual side-panel.
17. `Stepper.tsx` — Visual step tracker for multi-stage requests.
18. `ApprovalChain.tsx` — Multi-tiered approver state visualization.
19. `ChatInput.tsx` — Floating auto-expanding multiline composer.
20. `SystemStatusPill.tsx` — Micro-badge showing system operational state.
21. `StatusBadge.tsx` — Verified, Pending, Stale, or Blocked tags.
22. `EmptyState.tsx` — Instructional zero-state with recommended questions.
23. `SkeletonLoader.tsx` — Shimmer effects matching exact card boundaries.
24. `ConfirmModal.tsx` — Destructive action verification dialog.

---

## 14. Workflow Panel Patterns

### 14.1 Pattern 1: Multi-Step Approval (e.g., Leave / Condonation)
```
[ Step 1: Request Details ] ➔ [ Step 2: Policy Verification ] ➔ [ Step 3: Approver Chain ]
```
* **Step 1:** Form inputs (Dates, Medical note upload, Reason).
* **Step 2:** System calculates attendance impact (e.g., "Will reduce attendance from 76% to 73.5%").
* **Step 3:** Dynamic routing (Requires Class Incharge + Principal approval).
* **Action:** `[ Submit for Approval ]` with instant tracking ID creation.

### 14.2 Pattern 2: Exception Review (e.g., Hall Ticket Fee Hold)
* **Header:** Student Identifier & Outstanding Balance.
* **Policy Rule:** "No hall ticket if balance exceeds ₹5,000 without Principal sign-off."
* **Action Block:** `[ Grant 15-Day Extension ]` or `[ Reject with Notice ]`.

---

## 15. Trust, Governance, Audit, and Human-in-the-Loop UX

1. **Source System Provenance:** Every result card displays an authoritative badge (`Source: SIS Database`, `Rule: Exam Code §4.2`).
2. **Freshness Indicators:** Real-time timestamp indicating exact data sync moment (`Checked: 13-Sep-2026 10:45 UTC`).
3. **No Phantom Writes:** When an action modifies data, the drawer requires a double-confirmation click with reason logging.
4. **Audit Footers:** System outputs generate unique `Correlation IDs` tied directly to backend audit database rows (`AuditLog`).

---

## 16. Responsive Design Rules

* **Desktop (≥ 1280px):** Full 3-zone layout (Sidebar 64px, Center 60%, Right Workflow 40%).
* **Tablet (768px – 1279px):** Sidebar collapses to slim rail; Right Workflow slides in as an overlay drawer (400px width).
* **Mobile (< 768px):** Sidebar converts to bottom navigation bar; Shortcut Grid collapses to 2 columns; Right Workflow renders as a full-screen modal sheet.

---

## 17. Accessibility Checklist (WCAG 2.1 AA Compliant)

- [ ] All interactive elements accessible via `Tab` / `Shift+Tab`.
- [ ] Keyboard focus ring (`--sn-border-focus`, 2px offset) visible on all buttons, inputs, and shortcut cards.
- [ ] Contrast ratio between text and glass background strictly exceeds **4.5:1** for standard text and **3:1** for large headings.
- [ ] All data icons paired with accessible `aria-label` or visible text.
- [ ] `prefers-reduced-motion` media query respected: all slide and scale animations fall back to instant opacity changes.
- [ ] Screen readers announce conversational turns via `aria-live="polite"`.

---

## 18. Frontend Implementation Plan

1. **Directory Setup:**
   * Create `apps/admin-web/src/components/command/` for central workspace widgets.
   * Create `apps/admin-web/src/components/workflow/` for dynamic right-side drawers.
2. **Layout Transformation:**
   * Upgrade `apps/admin-web/src/app/dashboard/layout.tsx` to mount `AppShell` with the slim icon rail and topbar.
   * Upgrade `apps/admin-web/src/app/dashboard/page.tsx` from static tiles to `UnifiedCommandWorkspace`.
3. **Component Registry Linking:**
   * Expand `apps/admin-web/src/lib/registry.tsx` to map all 14 response block types to their respective React widgets.

---

## 19. Backend Contract Requirements

1. **Router Enhancement:**
   * Support pattern-matched natural language queries for all primary student and faculty intents.
2. **Deterministic Service Wrappers:**
   * Implement typed tool wrappers for `AttendanceService`, `ExamService`, `FeeService`, and `MasteryService`.
3. **Enforce Tenant Boundaries:**
   * Every tool strictly extracts `school_id` and `user_id` from the verified JWT context (`CurrentUser`), never from client input.

---

## 20. Phase-by-Phase Delivery Plan

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PHASE 0    │ ──> │   PHASE 1    │ ──> │   PHASE 2    │ ──> │   PHASE 3    │
│ Teacher Read │     │ Student Self │     │ Governed     │     │ Admin & Exam │
│ Workspace &  │     │ Service &    │     │ Workflow     │     │ Approvals &  │
│ UI Blocks    │     │ Attendance   │     │ Drawers      │     │ Interventions│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

* **Phase 0 (Complete & Certified):** Teacher workspace read mode, deterministic evidence synthesis, typed UI blocks.
* **Phase 1 (Active):** Chat-first home workspace, student attendance/timetable/fee shortcuts, unified 3-zone layout.
* **Phase 2:** Right-side workflow panel engine, leave requests, bonafide certificate generator.
* **Phase 3:** Faculty approval queue, exam cell exception management, student risk review.
* **Phase 4:** Voice input/output integration via Sarvam AI (Telugu, Hindi, English).
* **Phase 5:** Cross-institutional analytics, predictive retention modeling, autonomous policy RAG.

---
*StudyNexs Product Design Pack — Single Source of Truth for Chat-First Academic Command Workspace.*
