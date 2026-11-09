"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { LearnerReportCardView } from "@/components/results/LearnerReportCards";
import { PARENT_NAV } from "@/lib/portal-nav";

export default function ParentReportCardPage() {
  const { studentId, reportId } = useParams<{ studentId: string; reportId: string }>();
  return (
    <PortalShell title="Report card" subtitle="Approved by the class teacher" nav={PARENT_NAV}>
      <Link href={`/parent/child/${studentId}/results`} className="btn btn-ghost gw-btn-sm" style={{ marginBottom: 12 }}>
        ← All results
      </Link>
      <LearnerReportCardView endpoint={`/api/v1/portal/child/${studentId}/report-cards/${reportId}`} />
    </PortalShell>
  );
}
