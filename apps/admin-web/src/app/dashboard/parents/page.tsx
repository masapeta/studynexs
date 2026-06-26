"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { PersonMono } from "@/components/briefing/PersonMono";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { CalendarDays, MapPin, Phone, Plus } from "lucide-react";

type ParentRow = {
  id: string;
  name: string;
  email?: string | null;
  mobile?: string | null;
  relationship: string;
  children: string[];
  child_label: string;
};

type NoticeItem = {
  id: string;
  title: string;
  content: string;
  audience: string;
  created_at?: string;
};

type EventItem = {
  id: string;
  title: string;
  event_date: string;
  event_time?: string | null;
  venue?: string | null;
};

function meetingTag(dateStr: string) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.ceil((d.getTime() - now.getTime()) / 86400000);
  if (diff <= 1) return { label: "Tomorrow", tone: "red" as const };
  if (diff <= 7) return { label: "This week", tone: "brass" as const };
  return { label: "Upcoming", tone: "gray" as const };
}

export default function ParentsPage() {
  const [parents, setParents] = useState<ParentRow[]>([]);
  const [notices, setNotices] = useState<NoticeItem[]>([]);
  const [meetings, setMeetings] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<{ data: { parents: ParentRow[] } }>("/api/v1/ops/parents-directory"),
      api<{ data: NoticeItem[] }>("/api/v1/notices"),
      api<{ data: EventItem[] }>("/api/v1/ops/events"),
    ])
      .then(([pRes, nRes, eRes]) => {
        setParents(pRes.data?.parents || []);
        const parentNotices = (nRes.data || []).filter(
          (n) => n.audience === "external" || n.audience === "parents"
        );
        setNotices(parentNotices.slice(0, 4));
        const sorted = [...(eRes.data || [])].sort(
          (a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime()
        );
        setMeetings(
          sorted.filter(
            (e) =>
              /parent|meeting|conference|ptm/i.test(e.title) ||
              /parent|meeting/i.test(e.venue || "")
          ).slice(0, 4)
        );
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load parents data")))
      .finally(() => setLoading(false));
  }, []);

  const directory = useMemo(() => parents.slice(0, 12), [parents]);

  return (
    <PageShell title="Parents" subtitle="Family communication, meetings, and directory">
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      {loading ? (
        <div className="gw-center">
          <div className="spinner" />
        </div>
      ) : (
        <>
          <div className="parents-top-grid">
            <div className="gw-card gw-card-pad">
              <h3 className="gw-list-title" style={{ marginBottom: 16 }}>
                Parent notices
              </h3>
              {notices.length === 0 ? (
                <p className="gw-muted">No recent parent-facing notices.</p>
              ) : (
                <div className="parents-messages">
                  {notices.map((m) => (
                    <div key={m.id} className="parents-message-row">
                      <PersonMono name={m.title.slice(0, 1)} size={36} />
                      <div>
                        <div className="gw-list-title">{m.title}</div>
                        <div className="gw-list-meta">{m.content.slice(0, 80)}…</div>
                      </div>
                      <StatusBadge tone="brass">{m.audience}</StatusBadge>
                    </div>
                  ))}
                </div>
              )}
              <Link href="/dashboard/notices" className="briefing-link" style={{ marginTop: 12, display: "inline-block" }}>
                View all notices →
              </Link>
            </div>

            <div className="gw-card gw-card-pad">
              <h3 className="gw-list-title" style={{ marginBottom: 16 }}>
                Parent meetings
              </h3>
              {meetings.length === 0 ? (
                <p className="gw-muted">No parent meetings on the calendar.</p>
              ) : (
                <div className="parents-meetings">
                  {meetings.map((m) => {
                    const tag = meetingTag(m.event_date);
                    return (
                      <div key={m.id} className="parents-meeting-row">
                        <div>
                          <div className="gw-list-title">{m.title}</div>
                          <div className="gw-list-meta">
                            <CalendarDays size={12} style={{ display: "inline", marginRight: 4 }} />
                            {m.event_date}
                            {m.event_time ? ` · ${m.event_time}` : ""}
                          </div>
                          {m.venue && (
                            <div className="gw-list-meta">
                              <MapPin size={12} style={{ display: "inline", marginRight: 4 }} />
                              {m.venue}
                            </div>
                          )}
                        </div>
                        <StatusBadge tone={tag.tone}>{tag.label}</StatusBadge>
                      </div>
                    );
                  })}
                </div>
              )}
              <Link href="/dashboard/events" className="btn btn-ghost gw-btn-sm" style={{ marginTop: 16, width: "100%" }}>
                <Plus size={14} /> Schedule meeting
              </Link>
            </div>
          </div>

          <div className="gw-card gw-card-pad" style={{ marginTop: 20 }}>
            <h3 className="gw-list-title" style={{ marginBottom: 16 }}>
              Parent directory
            </h3>
            {directory.length === 0 ? (
              <p className="gw-muted">No linked parents yet.</p>
            ) : (
              <div className="parents-directory-grid">
                {directory.map((p) => (
                  <div key={p.id} className="parents-directory-card">
                    <PersonMono name={p.name} size={36} />
                    <div>
                      <div className="gw-list-title">{p.name}</div>
                      <div className="gw-list-meta">{p.child_label}</div>
                      {p.mobile && (
                        <div className="gw-list-meta">
                          <Phone size={12} style={{ display: "inline", marginRight: 4 }} />
                          {p.mobile}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </PageShell>
  );
}
