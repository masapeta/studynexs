/** Locale-aware formatting for Indian school UI. */
export function inr(n: number | null | undefined): string {
  const v = Number(n ?? 0);
  return "₹" + v.toLocaleString("en-IN");
}

export function briefingDate(d = new Date()): string {
  return d.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

export function todayDayKey(d = new Date()): string {
  const keys = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
  ];
  return keys[d.getDay()];
}

export function parseHm(t: string): number {
  const [h, m] = t.split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

/** Numeric portion of stored grade labels (e.g. "Class 10" → 10). */
export function classGradeNumber(grade: string): number {
  const m = grade.match(/(\d+)/);
  return m ? parseInt(m[1], 10) : 0;
}

/** Human label without duplicating "Grade Class …" when grade already includes "Class". */
export function formatClassLabel(grade: string, section: string): string {
  const g = grade.trim();
  if (/^class\s+/i.test(g)) {
    return `${g} — ${section}`;
  }
  return `Class ${g} — ${section}`;
}

export function sortClasses<T extends { grade: string; section: string }>(
  classes: T[] | null | undefined,
): T[] {
  const list = [...(classes ?? [])];
  return list.sort((a, b) => {
    const byGrade = classGradeNumber(a.grade) - classGradeNumber(b.grade);
    if (byGrade !== 0) return byGrade;
    return a.section.localeCompare(b.section);
  });
}

/** Month abbreviation + day for event date badges (e.g. Jun / 26). */
export function eventBadgeParts(iso: string) {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return { month: "--", day: "--" };
  const [, year, monthNum, dayNum] = m;
  const d = new Date(Number(year), Number(monthNum) - 1, 1);
  return {
    month: d.toLocaleDateString("en-IN", { month: "short" }),
    day: String(Number(dayNum)),
  };
}

/** ISO date (YYYY-MM-DD) → dd MMM yyyy for tables. */
export function formatDob(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}
