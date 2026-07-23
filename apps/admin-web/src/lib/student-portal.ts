import { Bell, BookOpen, Home, Sparkles } from "lucide-react";
import type { NavItem } from "@/components/PortalShell";

export const STUDENT_NAV: NavItem[] = [
  { href: "/student", label: "Home", icon: Home },
  { href: "/student/tutor", label: "AI Tutor", icon: Sparkles },
  { href: "/student/mastery", label: "Mastery", icon: BookOpen },
  { href: "/student/notices", label: "Notices", icon: Bell },
];

export type TutorStep = {
  id: string;
  title: string;
  narration: string;
  visual_kind: string;
  caption?: string;
};

export type TutorLesson = {
  lesson_key: string;
  topic: string;
  subject_name: string;
  mastery_pct?: number;
  trigger: string;
  mistake_summary?: string;
  steps: TutorStep[];
  pack_id?: string | null;
  concept_id?: string | null;
  concept_slug?: string | null;
};

export type DailyLearningPlan = {
  student_id: string;
  status: "ready" | "empty" | string;
  title: string;
  reason: string;
  recommended_action: string;
  topic?: string | null;
  mastery_topic?: string | null;
  mastery_pct?: number | null;
  lesson_key?: string | null;
  pack_id?: string | null;
  concept_id?: string | null;
  concept_slug?: string | null;
  source_count: number;
  grounded: boolean;
  fallback: boolean;
  evidence_summary: string;
  next_steps: string[];
};
