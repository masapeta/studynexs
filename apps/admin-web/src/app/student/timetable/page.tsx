"use client";

import PortalShell from "@/components/PortalShell";
import { LearnerTimetable } from "@/components/results/LearnerTimetable";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentTimetablePage() {
  return (
    <PortalShell title="Timetable" subtitle="Your class schedule" nav={STUDENT_NAV}>
      <LearnerTimetable endpoint="/api/v1/portal/timetable" />
    </PortalShell>
  );
}
