"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { LearnerResultDetailView } from "@/components/results/LearnerResults";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentResultDetailPage() {
  const { examId } = useParams<{ examId: string }>();
  return (
    <PortalShell title="Result" subtitle="Released by your teacher" nav={STUDENT_NAV}>
      <Link href="/student/results" className="btn btn-ghost gw-btn-sm" style={{ marginBottom: 12 }}>
        ← All results
      </Link>
      <LearnerResultDetailView endpoint={`/api/v1/portal/results/${examId}`} />
    </PortalShell>
  );
}
