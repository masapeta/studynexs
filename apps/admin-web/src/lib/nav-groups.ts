import type { ElementType } from "react";
import {
  Award,
  Banknote,
  BarChart3,
  BookOpen,
  Bus,
  CalendarDays,
  ClipboardCheck,
  FileText,
  GraduationCap,
  HeartHandshake,
  LayoutDashboard,
  Megaphone,
  NotebookPen,
  Receipt,
  School,
  Sparkles,
  Target,
  UserPlus,
  UserCog,
  Wallet,
} from "lucide-react";
import type { UserPermissions } from "./permissions";

export type NavItem = {
  label: string;
  href: string;
  icon: ElementType;
  module?: string;
  perm?: keyof UserPermissions;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, perm: "can_view_dashboard" },
      { label: "Reports", href: "/dashboard/reports", icon: BarChart3, perm: "can_view_dashboard" },
    ],
  },
  {
    label: "People",
    items: [
      { label: "Students", href: "/dashboard/students", icon: GraduationCap, perm: "can_manage_students" },
      { label: "Staff & HR", href: "/dashboard/staff", icon: UserCog, perm: "can_manage_staff" },
      { label: "Parents", href: "/dashboard/parents", icon: HeartHandshake, perm: "can_manage_students" },
      { label: "Admissions", href: "/dashboard/admissions", icon: UserPlus, perm: "can_manage_students" },
    ],
  },
  {
    label: "Academics",
    items: [
      { label: "Classes", href: "/dashboard/classes", icon: School, perm: "can_view_classes" },
      { label: "Attendance", href: "/dashboard/attendance", icon: ClipboardCheck, module: "attendance", perm: "can_use_attendance" },
      { label: "Gradebook", href: "/dashboard/gradebook", icon: Award, module: "exams", perm: "can_use_exams" },
      { label: "Exams", href: "/dashboard/exams", icon: FileText, module: "exams", perm: "can_use_exams" },
      { label: "AI Papers", href: "/dashboard/ai-papers", icon: Sparkles, module: "ai_papers", perm: "can_use_ai_papers" },
      { label: "Topic Mastery", href: "/dashboard/mastery", icon: Target, module: "mastery", perm: "can_use_mastery" },
      { label: "Lesson Plans", href: "/dashboard/lesson-plans", icon: NotebookPen, perm: "can_use_exams" },
      { label: "Report Cards", href: "/dashboard/report-cards", icon: Award, module: "report_cards", perm: "can_use_report_cards" },
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
      { label: "Fees", href: "/dashboard/fees", icon: Wallet, module: "finance", perm: "can_use_finance" },
      { label: "Payroll", href: "/dashboard/payroll", icon: Banknote, module: "finance", perm: "can_use_finance" },
      { label: "Expenses", href: "/dashboard/expenses", icon: Receipt, module: "finance", perm: "can_use_finance" },
      { label: "Finance overview", href: "/dashboard/finance", icon: Wallet, module: "finance", perm: "can_use_finance" },
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
