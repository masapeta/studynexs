"use client";

import PortalShell from "@/components/PortalShell";
import NoticeFeed from "@/components/NoticeFeed";
import { PARENT_NAV } from "@/lib/portal-nav";

export default function ParentNoticesPage() {
  return (
    <PortalShell title="Notices" subtitle="School announcements" nav={PARENT_NAV}>
      <NoticeFeed />
    </PortalShell>
  );
}
