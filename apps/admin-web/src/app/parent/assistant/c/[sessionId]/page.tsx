"use client";

import { useParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import { PARENT_NAV } from "@/lib/portal-nav";

export default function ParentConversationPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <PortalShell title="Ask StudyNexs" nav={PARENT_NAV} chat sessionId={sessionId} />;
}
