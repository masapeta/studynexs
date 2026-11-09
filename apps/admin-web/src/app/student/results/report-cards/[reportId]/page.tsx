"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { LearnerReportCardView } from "@/components/results/LearnerReportCards";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentReportCardPage() {
  const { reportId } = useParams<{ reportId: string }>();
  return (
    <PortalShell title="Report card" subtitle="Approved by your teacher" nav={STUDENT_NAV}>
      <Link href="/student/results" className="btn btn-ghost gw-btn-sm" style={{ marginBottom: 12 }}>
        ← All results
      </Link>
      <LearnerReportCardView endpoint={`/api/v1/portal/report-cards/${reportId}`} />
    </PortalShell>
  );
}
