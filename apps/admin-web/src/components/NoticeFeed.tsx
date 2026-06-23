"use client";

import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { Card, EmptyState, Skeleton } from "@/components/ui/kit";
import { api, getApiErrorMessage } from "@/lib/api";

const PRIORITY_TONE: Record<string, string> = {
  urgent: "var(--danger)",
  high: "var(--danger)",
  medium: "var(--accent-dark)",
  low: "var(--text-muted)",
};

type Notice = { id: string; title: string; content: string; priority?: string; created_at?: string };

/** Shared notices feed for the parent & student portals. Renders the `content`
 *  field (the API's field — the old pages read a non-existent `body`). */
export default function NoticeFeed() {
  const [notices, setNotices] = useState<Notice[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/notices")
      .then((r) => setNotices(r.data || []))
      .catch((e) => {
        setError(getApiErrorMessage(e, "Failed to load notices"));
        setNotices([]);
      });
  }, []);

  if (error) return <EmptyState icon={Bell} title="Couldn't load notices" message={error} />;
  if (notices === null) {
    return (
      <>
        {[0, 1].map((i) => (
          <Card key={i}>
            <Skeleton h={14} w="60%" />
            <div style={{ height: 8 }} />
            <Skeleton h={12} w="90%" />
          </Card>
        ))}
      </>
    );
  }
  if (notices.length === 0) {
    return <EmptyState icon={Bell} title="No notices yet" message="School announcements will show up here." />;
  }
  return (
    <>
      {notices.map((n) => (
        <Card key={n.id}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "baseline" }}>
            <div style={{ fontWeight: 700, fontSize: 15 }}>{n.title}</div>
            {n.priority && n.priority !== "medium" && (
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", color: PRIORITY_TONE[n.priority] || "var(--text-muted)" }}>
                {n.priority}
              </span>
            )}
          </div>
          <p style={{ fontSize: 14, margin: "6px 0 0", lineHeight: 1.5, color: "var(--text-secondary)" }}>{n.content}</p>
          {n.created_at && (
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
              {new Date(n.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
            </div>
          )}
        </Card>
      ))}
    </>
  );
}
