// Per-school feature modules. enabled_modules (on the school) maps key -> boolean.
// Default ON unless listed in DEFAULT_OFF (new modules that need setup first).

export type ModuleDef = { key: string; label: string; desc: string; defaultOff?: boolean };

export const TOGGLEABLE_MODULES: ModuleDef[] = [
  { key: "ai_papers", label: "AI Question Papers", desc: "AI-generated board-style papers" },
  { key: "attendance", label: "Attendance", desc: "Daily attendance tracking" },
  { key: "exams", label: "Exams & Marks", desc: "Exams and marks entry" },
  { key: "report_cards", label: "Report Cards", desc: "Consolidated report cards + AI remarks" },
  { key: "timetable", label: "Timetable", desc: "Class period scheduling" },
  { key: "finance", label: "Finance / Fees", desc: "Fee collection and receipts" },
  { key: "notices", label: "Notices", desc: "Announcements to students/parents" },
  { key: "transport", label: "Transport", desc: "Bus routes and student transport", defaultOff: true },
  { key: "residential", label: "Residential / Hostel", desc: "Boarding and room allocation", defaultOff: true },
];

/** Resolve whether a module is on, given the school's saved map. */
export function isModuleOn(modules: Record<string, boolean>, def: ModuleDef): boolean {
  const v = modules[def.key];
  if (v === undefined) return !def.defaultOff;
  return v;
}
