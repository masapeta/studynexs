"use client";

import PortalShell from "@/components/PortalShell";
import { PARENT_NAV } from "@/lib/portal-nav";

export default function ParentAssistantPage() {
  return <PortalShell title="Ask StudyNexs" nav={PARENT_NAV} chat />;
}
