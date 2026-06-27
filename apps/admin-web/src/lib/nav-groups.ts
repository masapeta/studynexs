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
