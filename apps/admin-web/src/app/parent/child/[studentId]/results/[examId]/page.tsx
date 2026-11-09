"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { LearnerResultDetailView } from "@/components/results/LearnerResults";
import { PARENT_NAV } from "@/lib/portal-nav";

export default function ParentChildResultDetailPage() {
  const { studentId, examId } = useParams<{ studentId: string; examId: string }>();
  return (
    <PortalShell title="Result" subtitle="Released by the teacher" nav={PARENT_NAV}>
      <Link
        href={`/parent/child/${studentId}/results`}
        className="btn btn-ghost gw-btn-sm"
        style={{ marginBottom: 12 }}
      >
        ← All results
      </Link>
      <LearnerResultDetailView endpoint={`/api/v1/portal/child/${studentId}/results/${examId}`} />
    </PortalShell>
  );
}
