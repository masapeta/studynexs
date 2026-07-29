export type ExamType =
  | "unit_test"
  | "formative_assessment"
  | "summative_assessment"
  | "mid_term"
  | "final"
  | "assignment"
  | "quiz"
  | "slip_test"
  | "quarterly"
  | "half_yearly";

export const EXAM_TYPE_OPTIONS: { value: ExamType; label: string }[] = [
  { value: "unit_test", label: "Unit test" },
  { value: "formative_assessment", label: "Formative assessment" },
  { value: "summative_assessment", label: "Summative assessment" },
  { value: "slip_test", label: "Slip test" },
  { value: "quiz", label: "Quiz" },
  { value: "assignment", label: "Assignment" },
  { value: "quarterly", label: "Quarterly examination" },
  { value: "half_yearly", label: "Half-yearly examination" },
  { value: "mid_term", label: "Mid-term examination" },
  { value: "final", label: "Final examination" },
];

export function examTypeLabel(value: string): string {
  return (
    EXAM_TYPE_OPTIONS.find((option) => option.value === value)?.label ??
    value.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase())
  );
}
