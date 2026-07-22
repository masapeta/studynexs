/** Mirrors GET /api/v1/users/me/permissions — drives nav and action buttons. */
import { FINANCE, STUDENTS, TEACHING } from "./dashboard-routes";

export interface UserPermissions {
  role: string;
  is_admin: boolean;
  scoped_only: boolean;
  incharge_class_ids: string[];
  teaching_class_ids: string[];
  can_view_dashboard: boolean;
  can_view_classes: boolean;
  can_manage_students: boolean;
  can_manage_staff: boolean;
  can_manage_classes: boolean;
  can_use_ai_papers: boolean;
  can_use_attendance: boolean;
  can_use_exams: boolean;
  can_use_mastery: boolean;
  can_use_report_cards: boolean;
  can_view_timetable: boolean;
  can_edit_timetable: boolean;
  can_use_finance: boolean;
  can_view_notices: boolean;
  can_publish_notices: boolean;
  can_publish_class_notices: boolean;
  can_publish_internal_notices: boolean;
  can_use_settings: boolean;
  can_approve_question_papers: boolean;
  can_manage_curriculum: boolean;
}

export const EMPTY_PERMISSIONS: UserPermissions = {
  role: "",
  is_admin: false,
  scoped_only: true,
  incharge_class_ids: [],
  teaching_class_ids: [],
  can_view_dashboard: false,
  can_view_classes: false,
  can_manage_students: false,
  can_manage_staff: false,
  can_manage_classes: false,
  can_use_ai_papers: false,
  can_use_attendance: false,
  can_use_exams: false,
  can_use_mastery: false,
  can_use_report_cards: false,
  can_view_timetable: false,
  can_edit_timetable: false,
  can_use_finance: false,
  can_view_notices: true,
  can_publish_notices: false,
  can_publish_class_notices: false,
  can_publish_internal_notices: false,
  can_use_settings: false,
  can_approve_question_papers: false,
  can_manage_curriculum: false,
};

type NavGate = keyof UserPermissions;

const TEACHING_SUBROUTES: { prefix: string; gate: NavGate }[] = [
  { prefix: TEACHING.aiPapers, gate: "can_use_ai_papers" },
  { prefix: TEACHING.mastery, gate: "can_use_mastery" },
  { prefix: TEACHING.reportCards, gate: "can_use_report_cards" },
  { prefix: TEACHING.exams, gate: "can_use_exams" },
  { prefix: TEACHING.gradebook, gate: "can_use_exams" },
  { prefix: TEACHING.lessonPlans, gate: "can_use_exams" },
  { prefix: TEACHING.curriculumOnboarding, gate: "can_manage_curriculum" },
  { prefix: TEACHING.curriculum, gate: "can_use_exams" },
];

/** Nav item → permission flag. Core items without a gate are always shown when logged in. */
export const NAV_PERMISSION: Record<string, NavGate | undefined> = {
  "/dashboard": "can_view_dashboard",
  "/dashboard/students": "can_manage_students",
  "/dashboard/staff": "can_manage_staff",
  "/dashboard/classes": "can_view_classes",
  "/dashboard/attendance": "can_use_attendance",
  "/dashboard/timetable": "can_view_timetable",
  "/dashboard/finance": "can_use_finance",
  "/dashboard/teaching": "can_use_exams",
  "/dashboard/library": "can_view_notices",
  "/dashboard/notices": "can_view_notices",
  "/dashboard/events": "can_view_notices",
  "/dashboard/transport": "can_view_timetable",
  "/dashboard/residential": "can_view_timetable",
  "/dashboard/settings": "can_use_settings",
  // Legacy bookmarks (redirect to hub paths)
  "/dashboard/ai-papers": "can_use_ai_papers",
  "/dashboard/exams": "can_use_exams",
  "/dashboard/mastery": "can_use_mastery",
  "/dashboard/report-cards": "can_use_report_cards",
  "/dashboard/fees": "can_use_finance",
  "/dashboard/payroll": "can_use_finance",
  "/dashboard/expenses": "can_use_finance",
  "/dashboard/admissions": "can_manage_students",
  "/dashboard/parents": "can_manage_students",
  "/dashboard/reports": "can_view_dashboard",
  "/dashboard/gradebook": "can_use_exams",
  "/dashboard/lesson-plans": "can_use_exams",
  "/dashboard/platform": "can_use_settings",
  "/dashboard/platform/engineering": "can_use_settings",
};

export const PORTAL_ROLES = new Set(["parent", "student"]);

export function teachingHubAllowed(perms: UserPermissions | null): boolean {
  if (!perms) return false;
  return (
    perms.can_use_exams ||
    perms.can_use_ai_papers ||
    perms.can_use_mastery ||
    perms.can_use_report_cards
  );
}

export function navAllowed(href: string, perms: UserPermissions | null): boolean {
  if (!perms) return false;
  if (href === TEACHING.root) return teachingHubAllowed(perms);
  const gate = NAV_PERMISSION[href];
  if (!gate) return false;
  return Boolean(perms[gate]);
}

function teachingRouteAllowed(pathname: string, perms: UserPermissions): boolean {
  if (!teachingHubAllowed(perms)) return false;
  const sorted = [...TEACHING_SUBROUTES].sort((a, b) => b.prefix.length - a.prefix.length);
  for (const { prefix, gate } of sorted) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      return Boolean(perms[gate]);
    }
  }
  return true;
}

/** Check access for nested routes like /dashboard/classes/abc-123 */
export function routeAllowed(pathname: string, perms: UserPermissions | null): boolean {
  if (!perms) return false;
  if (PORTAL_ROLES.has(perms.role)) {
    return false;
  }
  if (pathname === "/dashboard") return navAllowed("/dashboard", perms);

  if (pathname.startsWith(`${STUDENTS.root}/`) || pathname === STUDENTS.root) {
    return navAllowed(STUDENTS.root, perms);
  }
  if (pathname.startsWith(`${FINANCE.root}/`) || pathname === FINANCE.root) {
    return navAllowed(FINANCE.root, perms);
  }
  if (pathname.startsWith(`${TEACHING.root}/`) || pathname === TEACHING.root) {
    return teachingRouteAllowed(pathname, perms);
  }
  if (pathname.startsWith("/dashboard/platform")) {
    return perms.role === "super_admin" || perms.role === "admin";
  }

  const prefixes = Object.keys(NAV_PERMISSION).sort((a, b) => b.length - a.length);
  for (const href of prefixes) {
    if (href !== "/dashboard" && (pathname === href || pathname.startsWith(`${href}/`))) {
      return navAllowed(href, perms);
    }
  }
  return false;
}

export function portalHomeForRole(role: string): string {
  if (role === "parent") return "/parent";
  if (role === "student") return "/student";
  return "/dashboard";
}

export function roleLabel(role: string): string {
  switch (role) {
    case "super_admin":
      return "Principal";
    case "admin":
      return "Admin";
    case "class_incharge":
      return "Class Incharge";
    case "teacher":
      return "Subject Teacher";
    default:
      return role.replace(/_/g, " ");
  }
}
