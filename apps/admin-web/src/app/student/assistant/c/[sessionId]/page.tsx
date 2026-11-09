"use client";

import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentConversationPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <PortalShell title="Ask StudyNexs" nav={STUDENT_NAV} chat sessionId={sessionId} />;
}
