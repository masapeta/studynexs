"use client";

import { useEffect, useState } from "react";
import PortalShell from "@/components/PortalShell";
import { PARENT_NAV } from "@/lib/portal-nav";
import { api, getApiErrorMessage } from "@/lib/api";

export default function ParentNoticesPage() {
  const [notices, setNotices] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/notices")
      .then((r) => setNotices(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load notices")));
  }, []);

  return (
    <PortalShell title="Notices" subtitle="School announcements" nav={PARENT_NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {notices.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No notices yet.</p>
      ) : notices.map((n) => (
        <div key={n.id} className="portal-card">
          <div style={{ fontWeight: 700 }}>{n.title}</div>
          <p style={{ fontSize: 14, margin: "8px 0 0" }}>{n.body}</p>
        </div>
      ))}
    </PortalShell>
  );
}
