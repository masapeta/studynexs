"use client";

import PortalShell from "@/components/PortalShell";
import NoticeFeed from "@/components/NoticeFeed";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentNoticesPage() {
  return (
    <PortalShell title="Notices" subtitle="From your school" nav={STUDENT_NAV}>
      <NoticeFeed />
    </PortalShell>
  );
}
