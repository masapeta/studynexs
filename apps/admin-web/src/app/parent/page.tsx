"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, Bell, CalendarCheck, ChevronRight, MessageSquare, RefreshCw, Target, Users, Wallet } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { Card, EmptyState, ListRow, SectionHeader, SkeletonCard, StatTile } from "@/components/ui/kit";
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

type Notification = { id: string; title: string; body: string; link?: string | null; created_at?: string; is_read: boolean };

function safeParentNotificationLink(link: string | null | undefined): string | undefined {
  if (!link) return undefined;
  if (link.startsWith("/parent/")) return link;
  return undefined;
}

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
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState("");

  const [refreshKey, setRefreshKey] = useState(0);

  const retry = () => {
    setError("");
    setChildren(null);
    setRefreshKey((key) => key + 1);
  };

  useEffect(() => {
    let active = true;
    Promise.all([
      api<{ data: { children?: Child[] } }>("/api/v1/portal/context"),
      api<{ data: Notification[] }>("/api/v1/notifications"),
    ])
      .then(([ctxRes, notifRes]) => {
        if (!active) return;
        setChildren(ctxRes.data?.children ?? []);
        setNotifications((notifRes.data || []).slice(0, 5));
      })
      .catch((e) => {
        if (!active) return;
        setError(getApiErrorMessage(e, "We couldn't load your children's progress."));
        setChildren([]);
        setNotifications([]);
      });
    return () => {
      active = false;
    };
  }, [refreshKey]);

  const firstName = user?.full_name?.split(" ")[0] || "there";
  const totalPending = (children ?? []).reduce((sum, c) => sum + (c.fee_pending || 0), 0);

  return (
    <PortalShell title="Parent Portal" subtitle="Your children's progress" nav={PARENT_NAV}>
      <div className="ui-greeting">
        <div className="ui-greeting-hi">Hi, {firstName} 👋</div>
        <div className="ui-greeting-sub">Here&apos;s how your {children && children.length === 1 ? "child is" : "children are"} doing.</div>
      </div>

      {error ? (
        <EmptyState
          icon={AlertCircle}
          title="Couldn't load"
          message={error}
          action={
            <button className="btn btn-primary" style={{ width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)" }} onClick={retry}>
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
        <>
          {/* Fee summary */}
          <Card className="ui-fee-summary" onClick={() => router.push("/parent/fees")}>
            <div>
              <div className="ui-fee-label">Fee Summary</div>
              <div className="ui-fee-amount">
                {totalPending > 0 ? `₹${totalPending.toLocaleString("en-IN")}` : "All paid up"}
              </div>
              <div className="ui-fee-sub">{totalPending > 0 ? "Pending across your children" : "Nothing due right now"}</div>
            </div>
            <span className="ui-fee-cta">View details <ChevronRight size={16} /></span>
          </Card>

          {/* My children */}
          <SectionHeader
            title="My Children"
            action={
              <button
                type="button"
                onClick={() => router.push("/parent/children")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent)",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                View all
              </button>
            }
          />
          {children.map((child) => {
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
                  <ChevronRight size={18} style={{ color: "var(--text-muted)" }} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                  <StatTile icon={CalendarCheck} label="Attendance" tone={attTone} value={att != null ? `${att}%` : "—"} />
                  <StatTile icon={Wallet} label="Fees due" tone={feeTone} value={child.fee_pending > 0 ? `₹${child.fee_pending.toLocaleString("en-IN")}` : "Paid"} />
                  <StatTile icon={Target} label="Weak topics" tone={weakTone} value={child.weak_topic_count} />
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(`/parent/child/${child.student_id}`);
                  }}
                  style={{
                    marginTop: 12,
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    padding: "10px 14px",
                    borderRadius: "var(--radius-full)",
                    border: "1px solid color-mix(in srgb, var(--accent) 35%, transparent)",
                    background: "color-mix(in srgb, var(--accent) 12%, transparent)",
                    color: "var(--accent)",
                    fontWeight: 600,
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  <MessageSquare size={15} />
                  Parent Copilot — weekly summary
                </button>
              </Card>
            );
          })}

          {/* Notifications & alerts */}
          <SectionHeader title="Notifications & Alerts" />
          <Card padded={false}>
            {notifications.length === 0 ? (
              <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
                You&apos;re all caught up.
              </div>
            ) : (
              <div style={{ padding: "4px 14px" }}>
                {notifications.map((n) => (
                  <ListRow
                    key={n.id}
                    icon={Bell}
                    tone={n.is_read ? "default" : "accent"}
                    title={n.title}
                    subtitle={n.body}
                    onClick={
                      safeParentNotificationLink(n.link)
                        ? () => router.push(safeParentNotificationLink(n.link)!)
                        : undefined
                    }
                    chevron={!!safeParentNotificationLink(n.link)}
                  />
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </PortalShell>
  );
}
