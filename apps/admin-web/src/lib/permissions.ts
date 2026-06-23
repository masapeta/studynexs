/** Mirrors GET /api/v1/users/me/permissions — drives nav and action buttons. */
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
}

export const EMPTY_PERMISSIONS: UserPermissions = {
  role: "",
  is_admin: false,
  scoped_only: true,
  incharge_class_ids: [],
  teaching_class_ids: [],
  can_view_dashboard: true,
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
};

type NavGate = keyof UserPermissions;

/** Nav item → permission flag. Core items without a gate are always shown when logged in. */
export const NAV_PERMISSION: Record<string, NavGate | undefined> = {
  "/dashboard": "can_view_dashboard",
  "/dashboard/students": "can_manage_students",
  "/dashboard/staff": "can_manage_staff",
  "/dashboard/classes": "can_view_classes",
  "/dashboard/ai-papers": "can_use_ai_papers",
  "/dashboard/attendance": "can_use_attendance",
  "/dashboard/exams": "can_use_exams",
  "/dashboard/mastery": "can_use_mastery",
  "/dashboard/report-cards": "can_use_report_cards",
  "/dashboard/timetable": "can_view_timetable",
  "/dashboard/finance": "can_use_finance",
  "/dashboard/notices": "can_view_notices",
  "/dashboard/transport": undefined,
  "/dashboard/residential": undefined,
  "/dashboard/settings": "can_use_settings",
};

export function navAllowed(href: string, perms: UserPermissions | null): boolean {
  if (!perms) return false;
  const gate = NAV_PERMISSION[href];
  if (!gate) return true;
  return Boolean(perms[gate]);
}

/** Check access for nested routes like /dashboard/classes/abc-123 */
export function routeAllowed(pathname: string, perms: UserPermissions | null): boolean {
  if (!perms) return false;
  if (pathname === "/dashboard") return navAllowed("/dashboard", perms);
  const prefixes = Object.keys(NAV_PERMISSION).sort((a, b) => b.length - a.length);
  for (const href of prefixes) {
    if (href !== "/dashboard" && (pathname === href || pathname.startsWith(`${href}/`))) {
      return navAllowed(href, perms);
    }
  }
  return true;
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
