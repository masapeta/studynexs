"use client";

import { ModuleHubNav } from "./ModuleHubNav";
import { TEACHING } from "@/lib/dashboard-routes";

const TABS = [
  { href: TEACHING.exams, label: "Exams" },
  { href: TEACHING.gradebook, label: "Gradebook" },
  { href: TEACHING.reportCards, label: "Report cards" },
  { href: TEACHING.aiPapers, label: "AI papers" },
  { href: TEACHING.lessonPlans, label: "Lesson plans" },
  { href: TEACHING.mastery, label: "Topic mastery" },
];

export function TeachingHubNav() {
  return <ModuleHubNav tabs={TABS} ariaLabel="Teaching and assessment" />;
}
