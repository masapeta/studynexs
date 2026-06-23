"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, CalendarCheck, RefreshCw, Target, Users, Wallet } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { Card, EmptyState, SkeletonCard, StatTile } from "@/components/ui/kit";
import { PARENT_NAV } from "@/lib/portal-nav";
import { useAuth } from "@/lib/auth-context";
import { api, getApiErrorMessage } from "@/lib/api";

type Child = {
  student_id: string;
  name: string;
  class_label: string;
  roll_no?: string | null;
  attendance_pct?: number | null;
  fee_pending: number;
  weak_topic_count: number;
};

function Avatar({ name }: { name: string }) {
  return (
    <div
      style={{
        width: 46, height: 46, borderRadius: 23, flexShrink: 0,
        background: "linear-gradient(135deg, var(--accent), var(--accent-dark))",
        color: "#fff", fontWeight: 800, fontSize: 18,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      {(name || "?").charAt(0).toUpperCase()}
    </div>
  );
}

export default function ParentHomePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [children, setChildren] = useState<Child[] | null>(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    setChildren(null);
    api("/api/v1/portal/context")
      .then((r) => setChildren(r.data?.children ?? []))
      .catch((e) => setError(getApiErrorMessage(e, "We couldn't load your children's progress.")));
  }

  useEffect(load, []);

  const firstName = user?.full_name?.split(" ")[0] || "there";

  return (
    <PortalShell title="Parent Portal" subtitle="Your children's progress" nav={PARENT_NAV}>
      <div className="ui-greeting">
        <div className="ui-greeting-hi">Hi, {firstName} 👋</div>
        <div className="ui-greeting-sub">Here's how your {children && children.length === 1 ? "child is" : "children are"} doing.</div>
      </div>

      {error ? (
        <EmptyState
          icon={AlertCircle}
          title="Couldn't load"
          message={error}
          action={
            <button className="btn btn-primary" style={{ width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)" }} onClick={load}>
              <RefreshCw size={15} style={{ marginRight: 6 }} /> Try again
            </button>
          }
        />
      ) : children === null ? (
        <>
          <SkeletonCard />
          <SkeletonCard />
        </>
      ) : children.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No children linked yet"
          message="Your children will appear here once the school links them to your account."
        />
      ) : (
        children.map((child) => {
          const att = child.attendance_pct;
          const attTone = att == null ? "default" : att >= 75 ? "success" : att >= 50 ? "warning" : "danger";
          const feeTone = child.fee_pending > 0 ? "danger" : "success";
          const weakTone = child.weak_topic_count > 0 ? "warning" : "success";
          return (
            <Card key={child.student_id} onClick={() => router.push(`/parent/child/${child.student_id}`)}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
                <Avatar name={child.name} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{child.name}</div>
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                    {child.class_label}{child.roll_no ? ` · Roll ${child.roll_no}` : ""}
                  </div>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                <StatTile
                  icon={CalendarCheck}
                  label="Attendance"
                  tone={attTone}
                  value={att != null ? `${att}%` : "—"}
                />
                <StatTile
                  icon={Wallet}
                  label="Fees due"
                  tone={feeTone}
                  value={child.fee_pending > 0 ? `₹${child.fee_pending.toLocaleString("en-IN")}` : "Paid"}
                />
                <StatTile
                  icon={Target}
                  label="Weak topics"
                  tone={weakTone}
                  value={child.weak_topic_count}
                />
              </div>
            </Card>
          );
        })
      )}
    </PortalShell>
  );
}
