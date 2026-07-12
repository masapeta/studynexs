/** Canonical dashboard paths after IA consolidation. */

export const DASHBOARD = "/dashboard";

export const FINANCE = {
  root: "/dashboard/finance",
  fees: "/dashboard/finance/fees",
  payroll: "/dashboard/finance/payroll",
  expenses: "/dashboard/finance/expenses",
} as const;

export const STUDENTS = {
  root: "/dashboard/students",
  enrolled: "/dashboard/students",
  admissions: "/dashboard/students/admissions",
  guardians: "/dashboard/students/guardians",
} as const;

export const TEACHING = {
  root: "/dashboard/teaching",
  exams: "/dashboard/teaching/exams",
  gradebook: "/dashboard/teaching/gradebook",
  reportCards: "/dashboard/teaching/report-cards",
  aiPapers: "/dashboard/teaching/ai-papers",
  lessonPlans: "/dashboard/teaching/lesson-plans",
  documentIngest: "/dashboard/teaching/document-ingest",
  mastery: "/dashboard/teaching/mastery",
  masteryDigest: "/dashboard/teaching/mastery/digest",
  corrections: "/dashboard/teaching/exams/corrections",
  evaluate: (examId: string) => `/dashboard/teaching/exams/${examId}/evaluate`,
} as const;

export const PLATFORM = {
  root: "/dashboard/platform",
  engineering: "/dashboard/platform/engineering",
} as const;
