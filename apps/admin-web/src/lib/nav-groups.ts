import type { ElementType } from "react";
import {
  BookOpen,
  Bus,
  CalendarDays,
  ClipboardCheck,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Megaphone,
  School,
  UserCog,
  Wallet,
} from "lucide-react";
import type { UserPermissions } from "./permissions";
import { FINANCE, STUDENTS, TEACHING } from "./dashboard-routes";

export type NavItem = {
  label: string;
  href: string;
  icon: ElementType;
  module?: string;
  perm?: keyof UserPermissions;
  /** Show when the user has any of these permissions. */
  anyPerm?: (keyof UserPermissions)[];
  /** Restrict to these roles (e.g. super_admin, admin). */
  roles?: string[];
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const TEACHING_ANY_PERM: (keyof UserPermissions)[] = [
  "can_use_exams",
  "can_use_ai_papers",
  "can_use_mastery",
  "can_use_report_cards",
];

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, perm: "can_view_dashboard" },
    ],
  },
  {
    label: "People",
    items: [
      { label: "Students", href: STUDENTS.root, icon: GraduationCap, perm: "can_manage_students" },
      { label: "Staff & HR", href: "/dashboard/staff", icon: UserCog, perm: "can_manage_staff" },
    ],
  },
  {
    label: "Teaching",
    items: [
      {
        label: "Assessments",
        href: TEACHING.root,
        icon: FileText,
        anyPerm: TEACHING_ANY_PERM,
      },
      { label: "Classes", href: "/dashboard/classes", icon: School, perm: "can_view_classes" },
      {
        label: "Attendance",
        href: "/dashboard/attendance",
        icon: ClipboardCheck,
        module: "attendance",
        perm: "can_use_attendance",
      },
    ],
  },
  {
    label: "Operations",
    items: [
      { label: "Timetable", href: "/dashboard/timetable", icon: CalendarDays, module: "timetable", perm: "can_view_timetable" },
      { label: "Events", href: "/dashboard/events", icon: CalendarDays, perm: "can_view_notices" },
      { label: "Transport", href: "/dashboard/transport", icon: Bus, module: "transport", perm: "can_view_timetable" },
      { label: "Library", href: "/dashboard/library", icon: BookOpen, module: "library", perm: "can_view_notices" },
      { label: "Residential", href: "/dashboard/residential", icon: School, module: "residential", perm: "can_view_timetable" },
    ],
  },
  {
    label: "Finance",
    items: [
      { label: "Finance", href: FINANCE.root, icon: Wallet, module: "finance", perm: "can_use_finance" },
    ],
  },
  {
    label: "Communications",
    items: [
      { label: "Notices", href: "/dashboard/notices", icon: Megaphone, module: "notices", perm: "can_view_notices" },
    ],
  },
];

export const DEFAULT_OFF_MODULES = new Set(["transport", "residential"]);

export type Persona = "principal" | "admin" | "operations" | "incharge" | "teacher";

/** Shell persona from role + scope: a TEACHER-role user with incharge classes gets the incharge IA. */
export function personaForPermissions(perms: UserPermissions | null): Persona {
  if (!perms) return "teacher";
  if (perms.role === "super_admin") return "principal";
  if (perms.role === "admin") return "admin";
  if (perms.role === "operations" && !perms.incharge_class_ids.length && !perms.teaching_class_ids.length) {
    return "operations";
  }
  if (perms.incharge_class_ids.length > 0) return "incharge";
  return "teacher";
}

export function moduleVisible(m: string | undefined, modules: Record<string, boolean>): boolean {
  if (!m) return true;
  if (DEFAULT_OFF_MODULES.has(m)) return modules[m] === true;
  return modules[m] !== false;
}

/** Visible staff nav groups (permission + module gated). Empty groups are dropped. */
export function visibleNavGroups(
  perms: UserPermissions | null,
  modules: Record<string, boolean>,
  allowed: (href: string, perms: UserPermissions | null) => boolean
): NavGroup[] {
  const itemVisible = (item: NavItem) => {
    if (!moduleVisible(item.module, modules)) return false;
    if (item.roles && perms && !item.roles.includes(perms.role)) return false;
    if (item.anyPerm && perms) {
      if (!item.anyPerm.some((p) => perms[p])) return false;
    } else if (item.perm && perms && !perms[item.perm]) {
      return false;
    }
    return allowed(item.href, perms);
  };
  return NAV_GROUPS.map((g) => ({ ...g, items: g.items.filter(itemVisible) })).filter(
    (g) => g.items.length > 0
  );
}
