/**
 * Governed academic action registry — the built-in "Act" layer of the
 * chat-first workspace. Every action is LIVE: clicking it runs the same
 * deterministic intent router as the composer, which either navigates to a real
 * governed page, pulls verified data from a real tenant-scoped endpoint, or runs
 * a real backend tool. No "coming soon", no fabricated data.
 */
import type { ElementType } from "react";
import {
  AlertTriangle,
  BookOpen,
  CalendarClock,
  ClipboardCheck,
  FileText,
  GraduationCap,
  LineChart,
  Megaphone,
  ShieldCheck,
  UserCheck,
  Users,
  Wallet,
} from "lucide-react";

export type WorkspaceRole = "admin" | "teacher" | "parent" | "student";

export interface WorkspaceActionDef {
  id: string;
  label: string;
  description: string;
  icon: ElementType;
  /** The natural-language intent this action runs through the router. It resolves
   *  to a real navigation, data pull, or backend tool — never a stub. */
  intent: string;
}

/* ── Student ───────────────────────────────────────────────────────────── */
const STUDENT_ACTIONS: WorkspaceActionDef[] = [
  { id: "tutor", label: "AI Tutor", description: "Learn weak concepts with guided help", icon: GraduationCap, intent: "Open AI tutor" },
  { id: "mastery", label: "My mastery", description: "Topic-wise progress and weak areas", icon: LineChart, intent: "Show my mastery" },
  { id: "notices", label: "Notices", description: "Announcements from your school", icon: Megaphone, intent: "Go to notices" },
];

/* ── Teacher / faculty ─────────────────────────────────────────────────── */
const TEACHER_ACTIONS: WorkspaceActionDef[] = [
  {
    id: "learning-evidence",
    label: "Student learning evidence",
    description: "Verified evidence for a student in your class",
    icon: ShieldCheck,
    intent: "Show learning evidence for a student in my class",
  },
  { id: "school-overview", label: "School overview", description: "Live student, teacher & class counts", icon: Users, intent: "School overview" },
  { id: "attendance", label: "Attendance", description: "Open the attendance workspace", icon: ClipboardCheck, intent: "Open attendance" },
  { id: "assessments", label: "Assessments", description: "Exams, gradebook & AI papers", icon: FileText, intent: "Open assessments" },
  { id: "curriculum", label: "Curriculum", description: "Packs, lessons & mastery", icon: BookOpen, intent: "Open curriculum" },
];

/* ── Admin / principal / exam cell ─────────────────────────────────────── */
const ADMIN_ACTIONS: WorkspaceActionDef[] = [
  { id: "school-overview", label: "School overview", description: "Live student, teacher & class counts", icon: Users, intent: "School overview" },
  { id: "fee-collection", label: "Fee collection", description: "Collected, pending & families with dues", icon: Wallet, intent: "Show fee collection status" },
  { id: "attendance", label: "Attendance today", description: "School-wide attendance snapshot", icon: UserCheck, intent: "School attendance today" },
  { id: "students", label: "Students", description: "Manage enrolment & admissions", icon: GraduationCap, intent: "Open students" },
  { id: "staff", label: "Staff & HR", description: "Manage teachers and staff", icon: Users, intent: "Open staff" },
  { id: "assessments", label: "Assessments", description: "Exams, gradebook & AI papers", icon: FileText, intent: "Open assessments" },
  { id: "finance", label: "Finance", description: "Fees, payroll & expenses", icon: Wallet, intent: "Open finance" },
  { id: "notices", label: "Notices", description: "School announcements", icon: Megaphone, intent: "Go to notices" },
];

/* ── Parent / guardian ─────────────────────────────────────────────────── */
const PARENT_ACTIONS: WorkspaceActionDef[] = [
  { id: "children", label: "My children", description: "Progress, attendance & feedback", icon: Users, intent: "Show my children" },
  { id: "fees", label: "Fees", description: "Dues, receipts and payments", icon: Wallet, intent: "Open fees" },
  { id: "notices", label: "Notices", description: "School announcements & alerts", icon: Megaphone, intent: "Go to notices" },
];

export const WORKSPACE_ACTIONS: Record<WorkspaceRole, WorkspaceActionDef[]> = {
  admin: ADMIN_ACTIONS,
  teacher: TEACHER_ACTIONS,
  parent: PARENT_ACTIONS,
  student: STUDENT_ACTIONS,
};

export function roleToWorkspaceRole(role: string | undefined): WorkspaceRole {
  if (role === "teacher" || role === "class_incharge") return "teacher";
  if (role === "parent") return "parent";
  if (role === "student") return "student";
  return "admin";
}

/** Suggested natural-language prompts per role for the composer. Lead with the role's
 *  real conversational capabilities (answered in-chat) before navigation, so each persona
 *  discovers what it can actually ask — never a capability the role can't execute. */
export const WORKSPACE_PROMPTS: Record<WorkspaceRole, string[]> = {
  admin: [
    "School overview",
    "Show fee collection status",
    "School attendance today",
    "Open students",
  ],
  teacher: [
    "Show learning evidence for a student in my class",
    "Open attendance",
    "Go to assessments",
  ],
  parent: [
    "How is my child doing?",
    "What is my child's attendance?",
    "Which subjects need improvement?",
    "What fees are due?",
  ],
  student: [
    "What should I study today?",
    "Which topics am I weak in?",
    "Explain my weakest topic",
  ],
};

/** Per-role hero (title + subtitle) for the empty chat state, so every persona sees a
 *  greeting that reflects its own world rather than a generic staff-flavored one. */
export interface WorkspaceHero {
  title: string;
  subtitle: string;
}

export const WORKSPACE_HERO: Record<WorkspaceRole, WorkspaceHero> = {
  admin: {
    title: "How can StudyNexs help run your school today?",
    subtitle:
      "Ask about students, attendance, fees, finance, staff, assessments, notices, or school performance.",
  },
  teacher: {
    title: "How can StudyNexs help your teaching today?",
    subtitle:
      "Ask about your classes, student learning evidence, attendance, assessments, and curriculum.",
  },
  parent: {
    title: "How is your child doing today?",
    subtitle:
      "Ask about your children's progress, attendance, topics to improve, fees, and school notices.",
  },
  student: {
    title: "What would you like to learn today?",
    subtitle:
      "Ask what to study, which topics you're weak in, open a lesson, or get help from your AI tutor.",
  },
};

/** The suggested prompts for a role (unknown/undefined -> admin, matching roleToWorkspaceRole). */
export function promptsForRole(role: string | undefined): string[] {
  return WORKSPACE_PROMPTS[roleToWorkspaceRole(role)];
}

/** The hero greeting for a role (unknown/undefined -> admin, matching roleToWorkspaceRole). */
export function heroForRole(role: string | undefined): WorkspaceHero {
  return WORKSPACE_HERO[roleToWorkspaceRole(role)];
}
