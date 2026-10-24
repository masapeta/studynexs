"use client";

import PortalShell from "@/components/PortalShell";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentAssistantPage() {
  return <PortalShell title="Ask StudyNexs" nav={STUDENT_NAV} chat />;
}
