"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { LearnerResultsList } from "@/components/results/LearnerResults";
import { PARENT_NAV } from "@/lib/portal-nav";

export default function ParentChildResultsPage() {
  const { studentId } = useParams<{ studentId: string }>();
  return (
    <PortalShell title="Results" subtitle="Released exam results" nav={PARENT_NAV}>
      <Link href={`/parent/child/${studentId}`} className="btn btn-ghost gw-btn-sm" style={{ marginBottom: 12 }}>
        ← Back to child
      </Link>
      <LearnerResultsList
        endpoint={`/api/v1/portal/child/${studentId}/results`}
        detailHref={(id) => `/parent/child/${studentId}/results/${id}`}
      />
    </PortalShell>
  );
}
