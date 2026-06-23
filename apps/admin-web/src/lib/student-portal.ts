export const STUDENT_NAV = [
  { href: "/student", label: "Home" },
  { href: "/student/tutor", label: "AI Tutor" },
  { href: "/student/mastery", label: "Mastery" },
  { href: "/student/notices", label: "Notices" },
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
};
