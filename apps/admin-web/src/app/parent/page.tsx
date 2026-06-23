"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";

const NAV = [
  { href: "/parent", label: "Home" },
  { href: "/parent/notices", label: "Notices" },
  { href: "/parent/fees", label: "Fees" },
  { href: "/demo/roadmap", label: "More" },
];

export default function ParentHomePage() {
  const [ctx, setCtx] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/portal/context")
      .then((r) => setCtx(r.data))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load")));
  }, []);

  return (
    <PortalShell title="Parent Portal" subtitle="Your children's progress" nav={NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!ctx ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : ctx.children?.length === 0 ? (
        <p>No linked children. Run <code>patch_demo_portal_logins.py</code> after seeding.</p>
      ) : (
        ctx.children.map((child: any) => (
          <Link key={child.student_id} href={`/parent/child/${child.student_id}`} className="portal-card" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
            <div style={{ fontWeight: 700, fontSize: 17 }}>{child.name}</div>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 12 }}>{child.class_label} · Roll {child.roll_no || "—"}</div>
            <div className="portal-stat-grid">
              <div className="portal-stat">
                <div className="portal-stat-label">Attendance</div>
                <div className="portal-stat-value">{child.attendance_pct != null ? `${child.attendance_pct}%` : "—"}</div>
              </div>
              <div className="portal-stat">
                <div className="portal-stat-label">Fee pending</div>
                <div className="portal-stat-value">₹{child.fee_pending}</div>
              </div>
              <div className="portal-stat">
                <div className="portal-stat-label">Weak topics</div>
                <div className="portal-stat-value">{child.weak_topic_count}</div>
              </div>
              <div className="portal-stat">
                <div className="portal-stat-label">AI insights</div>
                <div className="portal-stat-value" style={{ fontSize: 14 }}>Live</div>
              </div>
            </div>
            <div style={{ fontSize: 13, color: "var(--accent)", fontWeight: 600 }}>View full profile →</div>
          </Link>
        ))
      )}
    </PortalShell>
  );
}
