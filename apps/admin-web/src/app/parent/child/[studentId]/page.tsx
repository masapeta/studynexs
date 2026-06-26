"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CalendarCheck, MessageSquare, Target, Wallet } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { Card, SectionHeader, StatTile } from "@/components/ui/kit";
import { PARENT_NAV } from "@/lib/portal-nav";
import { api, getApiErrorMessage } from "@/lib/api";
import type { ParentChildProgress } from "@/lib/portal-types";

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return "";
  }
}

export default function ParentChildPage() {
  const params = useParams();
  const studentId = params.studentId as string;
  const [progress, setProgress] = useState<ParentChildProgress | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!studentId) return;
    api<{ data: ParentChildProgress }>(`/api/v1/portal/child/${studentId}/progress`)
      .then((res) => setProgress(res.data))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load child")));
  }, [studentId]);

  const att = progress?.attendance_pct;
  const attTone = att == null ? "default" : att >= 75 ? "success" : att >= 50 ? "warning" : "danger";
  const feeTone = (progress?.fee_pending ?? 0) > 0 ? "danger" : "success";
  const weakTone = (progress?.weak_topic_count ?? 0) > 0 ? "warning" : "success";

  return (
    <PortalShell title="Child profile" subtitle={progress?.name} nav={PARENT_NAV}>
      <Link href="/parent/children" style={{ fontSize: 13, marginBottom: 12, display: "inline-block" }}>
        ← All children
      </Link>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!progress ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : (
        <>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 12 }}>
            {progress.class_label}
            {progress.roll_no ? ` · Roll ${progress.roll_no}` : ""}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
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
              value={progress.fee_pending > 0 ? `₹${progress.fee_pending.toLocaleString("en-IN")}` : "Paid"}
            />
            <StatTile
              icon={Target}
              label="Weak topics"
              tone={weakTone}
              value={progress.weak_topic_count ?? progress.weak_topics.length}
            />
          </div>

          <SectionHeader title="Weak topics" />
          <Card>
            {progress.weak_topics.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                No weak topics yet — appears after marked exams.
              </p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {progress.weak_topics.map((topic) => (
                  <li key={`${topic.subject_name}-${topic.topic}`} style={{ marginBottom: 6 }}>
                    <span style={{ fontWeight: 600 }}>{topic.subject_name}</span>: {topic.topic_display}{" "}
                    <span style={{ color: "var(--text-muted)" }}>({Math.round(topic.mastery_pct)}%)</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <SectionHeader title="Teacher feedback" />
          {progress.feedbacks.length === 0 ? (
            <Card>
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                No teacher feedback shared yet. You&apos;ll see notes here when teachers notify you about learning
                gaps.
              </p>
            </Card>
          ) : (
            progress.feedbacks.map((feedback, index) => (
              <div key={`${feedback.topic}-${feedback.notified_at ?? index}`} style={{ marginBottom: 10 }}>
                <Card>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <MessageSquare size={15} style={{ color: "var(--accent)" }} />
                  <span style={{ fontWeight: 700, fontSize: 14 }}>
                    {feedback.subject_name} · {feedback.topic_display}
                  </span>
                  {feedback.notified_at && (
                    <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-muted)" }}>
                      {formatDate(feedback.notified_at)}
                    </span>
                  )}
                </div>
                <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "var(--text-secondary)" }}>
                  {feedback.narrative}
                </p>
                </Card>
              </div>
            ))
          )}
        </>
      )}
    </PortalShell>
  );
}
