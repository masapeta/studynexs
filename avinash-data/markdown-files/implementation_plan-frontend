# Role-Based Dashboard Architecture Plan

You are absolutely right. A generic dashboard doesn't work for a multi-tenant system with strict RBAC (Role-Based Access Control). A Teacher should not see school-wide fee collections, and an Admin does not need a "Take Attendance" shortcut.

We will architect the dashboard dynamically so that the Bento Grid renders widgets based on the logged-in user's `role`.

## Open Questions
> [!IMPORTANT]
> - Are there any specific metrics you want Operations staff to see that Admins shouldn't, or vice-versa? 
> - Should we keep the dark navy sidebar with an inverted (white) logo, or switch to a lighter sidebar theme to show the official Academix logo in its true colors?

## Proposed Changes

We will refactor `apps/staff-web/src/app/(dashboard)/dashboard/page.tsx` to serve as a role-router. It will dynamically mount specific sub-components based on `user.role`.

# Role-Based Dashboard Architecture (V2)

Based on a deep strategic review, the dashboards will not just display data—they will act as tailored **workflow engines** for each specific human role in the school. The UI will strictly separate *execution* from *strategy* to prevent noise and micromanagement.

### 1. Operations View ("The Live Control Room")
*Focus: Real-time Execution & Issue Resolution*
- **Office Admin**: Admissions CRM, pending fee follow-ups (action list, not analytics), pending parent queries, and visitor logs.
- **Floor Incharge**: Live dashboard of "Classes running vs Unattended." Real-time alerts for absent teachers. Substitution engine to assign available teachers instantly. 

### 2. Admin View (Principal / Management)
*Focus: Trends, Risks, and Decisions*
- **Health Snapshot**: Aggregated student/teacher attendance trends, financial health overview (monthly targets vs actuals).
- **Teacher Effectiveness**: Punctuality trends, classes taken vs assigned, syllabus completion rates.
- **Escalation Engine**: Auto-routed alerts that Operations failed to resolve (e.g., class unattended for >10 mins, severe fee defaults).

### 3. Teacher Views (The Hybrid Model)
*Focus: Ownership vs Delivery*
- **Class Teacher (Ownership)**: Acts as the "mini-admin" for one class. Sees the Class Health Engine (attendance %, behavior signals), Student 360 view (cross-subject performance), and acts as the primary Parent Communication Hub.
- **Subject Teacher (Execution)**: Period-wise dashboard. Lesson logging ("what was taught today"), homework assignment, marks entry, and syllabus tracker.
- *Hybrid Support*: If a user holds both roles, the UI intelligently merges these views without duplicating tasks.

### 4. Parent View ("Instagram for School Life")
*Focus: Unified Timeline & Actionable Alerts*
- **Multi-Child Switcher**: One tap context switch between children.
- **Daily Timeline Feed**: Chronological updates (9:00 AM marked present -> 1:00 PM Math homework assigned).
- **Action Center**: One place to clear pending items (Approve leave, Pay unified fees, View new marks). Smart grouping of notifications to prevent spam.

### 5. Student View ("The Daily Companion")
*Focus: Self-Service Execution & Healthy Gamification*
- **Today's Tasks**: Action-oriented list (Homework due, revise for tomorrow's test) rather than passive timetables.
- **Effort-Based Gamification**: Consistency streaks (homework, attendance) and progress percentages. **No toxic leaderboards or competitive XP.**
- **Doubt Resolution Flow**: Threaded questions routed to specific subject teachers to prevent chat chaos.
- **Missed Class Recovery**: Immediate access to "What was taught today" for absent students.

## Verification Plan
- Implement the router logic in `page.tsx`.
- Create mock roles in the frontend state or test with actual seeded Admin/Teacher credentials.
- Render the dashboard using the browser tool to visually confirm that a Teacher only sees academic widgets and an Admin sees the high-level financial/attendance bento layout.
