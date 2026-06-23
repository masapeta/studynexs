"use client";

import Link from "next/link";
import PortalShell from "@/components/PortalShell";

const NAV = [
  { href: "/teacher", label: "Home" },
  { href: "/dashboard/ai-papers", label: "AI Papers" },
  { href: "/dashboard/exams", label: "Exams" },
  { href: "/dashboard/mastery", label: "Mastery" },
];

export default function TeacherHomePage() {
  return (
    <PortalShell title="Teacher" subtitle="Mobile-friendly shortcuts" nav={NAV}>
      <div className="portal-card">
        <div style={{ fontWeight: 700, marginBottom: 12 }}>Quick actions</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <Link href="/dashboard/ai-papers" className="btn btn-outline" style={{ textAlign: "center" }}>Generate AI question papers</Link>
          <Link href="/dashboard/exams" className="btn btn-outline" style={{ textAlign: "center" }}>Exams & answer-sheet eval</Link>
          <Link href="/dashboard/mastery" className="btn btn-outline" style={{ textAlign: "center" }}>Class mastery heatmap</Link>
          <Link href="/dashboard/attendance" className="btn btn-outline" style={{ textAlign: "center" }}>Mark attendance</Link>
        </div>
      </div>
      <div className="portal-card">
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Full admin</div>
        <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "0 0 12px" }}>
          Open the desktop dashboard for fees, notices, and school settings.
        </p>
        <Link href="/dashboard" className="btn btn-primary" style={{ width: "100%", textAlign: "center" }}>Open dashboard</Link>
      </div>
    </PortalShell>
  );
}
