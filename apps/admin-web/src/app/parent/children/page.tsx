"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  CalendarCheck,
  ChevronRight,
  MessageSquare,
  RefreshCw,
  Target,
  Users,
  Wallet,
} from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { Card, EmptyState, SectionHeader, SkeletonCard, StatTile } from "@/components/ui/kit";
import { PARENT_NAV } from "@/lib/portal-nav";
import { api, getApiErrorMessage } from "@/lib/api";
import type { ParentChildProgress } from "@/lib/portal-types";

function Avatar({ name }: { name: string }) {
  return (
    <div
      style={{
        width: 46,
        height: 46,
        borderRadius: 23,
        flexShrink: 0,
        background: "linear-gradient(135deg, var(--accent), var(--accent-dark))",
        color: "#fff",
        fontWeight: 800,
        fontSize: 18,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {(name || "?").charAt(0).toUpperCase()}
    </div>
  );
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return "";
  }
}

export default function ParentChildrenPage() {
  const router = useRouter();
  const [children, setChildren] = useState<ParentChildProgress[] | null>(null);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  const retry = () => {
    setError("");
    setChildren(null);
    setRefreshKey((key) => key + 1);
  };

  useEffect(() => {
    let active = true;
    api<{ data: ParentChildProgress[] }>("/api/v1/portal/parent/children-progress")
      .then((res) => {
        if (!active) return;
        setChildren(res.data ?? []);
      })
      .catch((e) => {
        if (!active) return;
        setError(getApiErrorMessage(e, "We couldn't load your children's progress."));
        setChildren([]);
      });
    return () => {
      active = false;
    };
  }, [refreshKey]);

  return (
    <PortalShell title="My Children" subtitle="Progress, feedback & weak topics" nav={PARENT_NAV}>
      {error ? (
        <EmptyState
          icon={AlertCircle}
          title="Couldn't load"
          message={error}
          action={
            <button
              className="btn btn-primary"
              style={{ width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)" }}
              onClick={retry}
            >
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
          const weakTone = (child.weak_topic_count ?? child.weak_topics.length) > 0 ? "warning" : "success";
          const latestFeedback = child.feedbacks[0];

          return (
            <Card key={child.student_id} onClick={() => router.push(`/parent/child/${child.student_id}`)}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
                <Avatar name={child.name} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{child.name}</div>
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                    {child.class_label}
                    {child.roll_no ? ` · Roll ${child.roll_no}` : ""}
                  </div>
                </div>
                <ChevronRight size={18} style={{ color: "var(--text-muted)" }} />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 14 }}>
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
                  value={child.weak_topic_count ?? child.weak_topics.length}
                />
              </div>

              {child.weak_topics.length > 0 && (
                <div style={{ marginBottom: latestFeedback ? 12 : 0 }}>
                  <SectionHeader title="Weak topics" />
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--text-secondary)" }}>
                    {child.weak_topics.slice(0, 3).map((topic) => (
                      <li key={`${topic.subject_name}-${topic.topic}`}>
                        {topic.subject_name}: {topic.topic_display} ({Math.round(topic.mastery_pct)}%)
                      </li>
                    ))}
                    {child.weak_topics.length > 3 && (
                      <li style={{ color: "var(--text-muted)" }}>+{child.weak_topics.length - 3} more</li>
                    )}
                  </ul>
                </div>
              )}

              {latestFeedback && (
                <div
                  style={{
                    padding: "10px 12px",
                    borderRadius: "var(--radius-md)",
                    background: "var(--surface-2)",
                    fontSize: 13,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, fontWeight: 600 }}>
                    <MessageSquare size={14} />
                    Teacher feedback
                    {latestFeedback.notified_at && (
                      <span style={{ fontWeight: 400, color: "var(--text-muted)", marginLeft: "auto" }}>
                        {formatDate(latestFeedback.notified_at)}
                      </span>
                    )}
                  </div>
                  <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>
                    {latestFeedback.subject_name} · {latestFeedback.topic_display}
                  </div>
                  <p style={{ margin: 0, lineHeight: 1.45 }}>
                    {latestFeedback.narrative.length > 140
                      ? `${latestFeedback.narrative.slice(0, 140)}…`
                      : latestFeedback.narrative}
                  </p>
                  {child.feedbacks.length > 1 && (
                    <div style={{ marginTop: 6, fontSize: 12, color: "var(--accent)" }}>
                      +{child.feedbacks.length - 1} more feedback{child.feedbacks.length > 2 ? "s" : ""}
                    </div>
                  )}
                </div>
              )}
            </Card>
          );
        })
      )}
    </PortalShell>
  );
}
