/**
 * Deterministic client-side intent router for the command workspace.
 *
 * Ask -> (decide) -> Act. Before any model/tool call, classify the request into:
 *  - "navigate": open an existing governed page (e.g. "show students", "open fees")
 *  - "query":    pull verified data via the workspace orchestrator (backend tool)
 *  - "guide":    no confident match -> a helpful response with quick links, never silence
 *
 * This keeps navigation instant and free (no LLM), reserves the backend for real
 * data pulls, and guarantees the user always gets a useful response.
 */
import type { UserPermissions } from "@/lib/permissions";
import { navAllowed } from "@/lib/permissions";
import type { WorkspaceRole } from "@/lib/workspace-actions";

export interface NavTarget {
  label: string;
  href: string;
}

/** A governed inline data pull — reuses an existing, tenant-scoped REST endpoint
 *  and renders verified metrics in the workspace (no LLM, deterministic). */
export interface DataQuery {
  id: string;
  title: string;
  endpoint: string;
  source: string;
  /** Extract labelled metrics from the endpoint's `data` payload. */
  metrics: Array<{ label: string; from: string; format?: "number" | "money" | "percent" }>;
  /** Optional deep-link shown as a follow-up action. */
  href?: string;
  hrefLabel?: string;
}

export type IntentResult =
  | { kind: "navigate"; target: NavTarget; reason: string }
  | { kind: "data"; query: DataQuery }
  | { kind: "query"; text: string }
  | { kind: "guide"; suggestions: NavTarget[] };

interface NavRule {
  href: string;
  label: string;
  /** Any of these keywords (word-ish match) routes here. */
  keywords: string[];
}

/* Staff navigation vocabulary → real dashboard routes. */
const STAFF_NAV_RULES: NavRule[] = [
  { href: "/dashboard/students", label: "Students", keywords: ["student", "students", "enrolment", "enrollment", "admission", "admissions"] },
  { href: "/dashboard/staff", label: "Staff & HR", keywords: ["staff", "teacher", "teachers", "hr", "employee", "employees"] },
  { href: "/dashboard/attendance", label: "Attendance", keywords: ["attendance", "present", "absent"] },
  { href: "/dashboard/finance", label: "Finance", keywords: ["finance", "fee", "fees", "payment", "payments", "invoice", "dues", "payroll", "expense", "expenses"] },
  { href: "/dashboard/classes", label: "Classes", keywords: ["class", "classes", "section", "sections"] },
  { href: "/dashboard/timetable", label: "Timetable", keywords: ["timetable", "schedule", "period", "periods"] },
  { href: "/dashboard/teaching", label: "Assessments", keywords: ["exam", "exams", "assessment", "assessments", "gradebook", "marks", "report card", "report cards", "question paper", "lesson plan", "mastery", "curriculum"] },
  { href: "/dashboard/notices", label: "Notices", keywords: ["notice", "notices", "announcement", "announcements", "circular", "circulars"] },
  { href: "/dashboard/events", label: "Events", keywords: ["event", "events", "calendar"] },
  { href: "/dashboard/library", label: "Library", keywords: ["library", "book", "books"] },
  { href: "/dashboard/transport", label: "Transport", keywords: ["transport", "bus", "route", "routes"] },
  { href: "/dashboard/settings", label: "Settings", keywords: ["setting", "settings", "configuration", "configure"] },
];

const PARENT_NAV_RULES: NavRule[] = [
  { href: "/parent/children", label: "Children", keywords: ["child", "children", "kid", "progress"] },
  { href: "/parent/fees", label: "Fees", keywords: ["fee", "fees", "payment", "dues", "invoice"] },
  { href: "/parent/notices", label: "Notices", keywords: ["notice", "notices", "announcement", "circular"] },
];

const STUDENT_NAV_RULES: NavRule[] = [
  { href: "/student/tutor", label: "AI Tutor", keywords: ["tutor", "learn", "explain", "study", "practice", "revise"] },
  { href: "/student/mastery", label: "Mastery", keywords: ["mastery", "weak", "topics", "progress", "marks"] },
  { href: "/student/notices", label: "Notices", keywords: ["notice", "notices", "announcement", "circular"] },
];

/** Verbs that strongly signal a navigation ("take me there") intent. */
const NAV_VERBS = /\b(open|go to|navigate|take me to|show me the|view the|manage)\b/i;
/** Verbs that signal a data pull. */
const QUERY_VERBS = /\b(how many|list|what is|what's|show|which|report|status|summary|count|are there|do i have|pending)\b/i;

function rulesForRole(role: WorkspaceRole): NavRule[] {
  if (role === "parent") return PARENT_NAV_RULES;
  if (role === "student") return STUDENT_NAV_RULES;
  return STAFF_NAV_RULES;
}

function matchNav(text: string, rules: NavRule[]): NavRule | null {
  const lower = ` ${text.toLowerCase()} `;
  let best: NavRule | null = null;
  let bestScore = 0;
  for (const rule of rules) {
    let score = 0;
    for (const kw of rule.keywords) {
      if (lower.includes(` ${kw} `) || lower.includes(`${kw}s `) || lower.includes(` ${kw},`)) {
        score += kw.length; // longer keyword = more specific
      }
    }
    if (score > bestScore) {
      bestScore = score;
      best = rule;
    }
  }
  return bestScore > 0 ? best : null;
}

/** Known live data-pull patterns handled by the backend orchestrator today
 *  (teacher learning-evidence path via /workspace/turn). */
const LIVE_QUERY_PATTERNS: RegExp[] = [
  /learning\s+evidence/i,
  /mastery\s+evidence/i,
  /learning\s+report/i,
  /weak\s+concepts?\s+for/i,
  /recent\s+assessment\s+evidence/i,
];

function isLiveQuery(text: string): boolean {
  return LIVE_QUERY_PATTERNS.some((re) => re.test(text));
}

/** Governed inline data pulls backed by existing tenant-scoped REST endpoints.
 *  Each entry: keywords that trigger it + the endpoint + metrics to surface. */
interface DataRule {
  query: DataQuery;
  keywords: RegExp;
}

const STAFF_DATA_RULES: DataRule[] = [
  {
    keywords: /\b(how many students|student count|total students|number of students|school overview|school summary|students enrolled)\b/i,
    query: {
      id: "school-overview",
      title: "School overview",
      endpoint: "/api/v1/dashboard/summary",
      source: "Student Information System",
      metrics: [
        { label: "Students", from: "total_students", format: "number" },
        { label: "Teachers", from: "total_teachers", format: "number" },
        { label: "Classes", from: "total_classes", format: "number" },
        { label: "Attendance today", from: "school_attendance_percent", format: "percent" },
      ],
      href: "/dashboard/students",
      hrefLabel: "Open students",
    },
  },
  {
    keywords: /\b(fee|fees|collection|pending fees|dues|outstanding|fee status|how much collected|fee summary)\b/i,
    query: {
      id: "fee-stats",
      title: "Fee collection",
      endpoint: "/api/v1/fees/stats",
      source: "Fee System",
      metrics: [
        { label: "Collected", from: "total_collected", format: "money" },
        { label: "Pending", from: "pending_amount", format: "money" },
        { label: "Families with dues", from: "pending_families", format: "number" },
      ],
      href: "/dashboard/finance",
      hrefLabel: "Open finance",
    },
  },
  {
    keywords: /\b(attendance today|school attendance|attendance rate|attendance summary|how is attendance)\b/i,
    query: {
      id: "attendance-overview",
      title: "Attendance overview",
      endpoint: "/api/v1/dashboard/summary",
      source: "Attendance System",
      metrics: [
        { label: "Attendance today", from: "school_attendance_percent", format: "percent" },
        { label: "Marked", from: "attendance_marked_today", format: "number" },
        { label: "Enrolled", from: "attendance_enrolled", format: "number" },
      ],
      href: "/dashboard/attendance",
      hrefLabel: "Open attendance",
    },
  },
];

function matchData(text: string, rules: DataRule[]): DataQuery | null {
  for (const rule of rules) {
    if (rule.keywords.test(text)) return rule.query;
  }
  return null;
}

function dataRulesForRole(role: WorkspaceRole): DataRule[] {
  // Staff data pulls only for now (admin/teacher). Parent/student inline data
  // will be added when their governed summary endpoints are wired in.
  if (role === "admin" || role === "teacher") return STAFF_DATA_RULES;
  return [];
}

function defaultSuggestions(role: WorkspaceRole, perms: UserPermissions | null): NavTarget[] {
  const rules = rulesForRole(role);
  const isStaff = role === "admin" || role === "teacher";
  return rules
    .filter((r) => (isStaff ? navAllowed(r.href, perms) : true))
    .slice(0, 6)
    .map((r) => ({ label: r.label, href: r.href }));
}

export function classifyIntent(
  rawText: string,
  role: WorkspaceRole,
  perms: UserPermissions | null
): IntentResult {
  const text = rawText.trim();
  const rules = rulesForRole(role);
  const isStaff = role === "admin" || role === "teacher";

  // 1) Live data pulls handled by the teacher orchestrator (learning evidence).
  if (isLiveQuery(text)) {
    return { kind: "query", text };
  }

  // 2) Governed inline data pull via existing REST endpoint (counts, fees, attendance).
  //    Only when the phrasing is a data question, not a "take me there" request.
  if (!NAV_VERBS.test(text)) {
    const data = matchData(text, dataRulesForRole(role));
    if (data) {
      return { kind: "data", query: data };
    }
  }

  // 3) Navigation intent: explicit "open/go to" verb, or a strong noun match that
  //    isn't phrased as a data question.
  const nav = matchNav(text, rules);
  if (nav) {
    const permitted = !isStaff || navAllowed(nav.href, perms);
    const wantsNavigation = NAV_VERBS.test(text) || !QUERY_VERBS.test(text);
    if (permitted && wantsNavigation) {
      return {
        kind: "navigate",
        target: { label: nav.label, href: nav.href },
        reason: `Opening ${nav.label}.`,
      };
    }
  }

  // 3) No confident match → guide with quick links (never a dead end).
  return { kind: "guide", suggestions: defaultSuggestions(role, perms) };
}
