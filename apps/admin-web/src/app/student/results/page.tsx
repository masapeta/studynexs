"use client";

import PortalShell from "@/components/PortalShell";
import { LearnerResultsList } from "@/components/results/LearnerResults";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentResultsPage() {
  return (
    <PortalShell title="Results" subtitle="Released exam results" nav={STUDENT_NAV}>
      <LearnerResultsList endpoint="/api/v1/portal/results" detailHref={(id) => `/student/results/${id}`} />
    </PortalShell>
  );
}
