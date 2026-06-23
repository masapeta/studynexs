"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Clock, MapPin, BookOpen, Sparkles, AlertCircle,
  CalendarDays, CheckCircle2, Megaphone, ChevronRight, RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";

export type TeacherHome = {
  greeting: string;
  tagline: string;
  today_classes: {
    slot_id: string;
    class_id: string;
    subject_id: string;
    class_label: string;
    subject_name: string;
    period_number: number;
    start_time: string;
    end_time: string;
    room?: string | null;
    next_topic?: string | null;
    attendance_status: string;
    homework_pending: boolean;
    actions: { label: string; href: string; variant?: string }[];
  }[];
  pending_work: { kind: string; label: string; detail?: string | null; href: string; count: number }[];
  lesson_plan?: {
    id?: string | null;
    class_id: string;
    subject_id: string;
    class_label: string;
    subject_name: string;
    schedule_label: string;
    chapter?: string | null;
    topic?: string | null;
    segments: { duration_min: number; activity: string }[];
    status: string;
    can_edit?: boolean;
    can_approve?: boolean;
    actions: { label: string; href: string; variant?: string }[];
  } | null;
  weekly_timetable: {
    day: string;
    day_label: string;
    slots: { start_time: string; class_label: string; subject_name: string }[];
  }[];
  subject_progress: {
    class_id: string;
    subject_id: string;
    class_label: string;
    subject_name: string;
    average_mastery?: number | null;
    weak_concepts: string[];
    students_needing_attention: {
      student_id: string;
      student_name: string;
      reason: string;
      topic?: string | null;
    }[];
  }[];
  staff_notices: {
    id: string;
    title: string;
    content: string;
    priority: string;
    created_at?: string | null;
    acknowledged: boolean;
    can_acknowledge: boolean;
  }[];
  school_notices: {
    id: string;
    title: string;
    content: string;
    priority: string;
    created_at?: string | null;
    acknowledged: boolean;
    can_acknowledge: boolean;
  }[];
};

function attBadge(status: string) {
  if (status === "done") return { label: "Attendance done", color: "var(--success)", bg: "var(--success-light)" };
  if (status === "pending") return { label: "Attendance pending", color: "var(--warning)", bg: "var(--warning-light)" };
  return { label: "Class teacher marks", color: "var(--text-muted)", bg: "var(--bg)" };
}

export function TeacherCommandCenter({ data, onRefresh }: { data: TeacherHome; onRefresh?: () => void }) {
  const [ttFilter, setTtFilter] = useState<"week" | "today">("week");
  const [lpBusy, setLpBusy] = useState(false);

  const todayDow = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"][
    new Date().getDay()
  ];
  const filteredTt =
    ttFilter === "today"
      ? data.weekly_timetable.filter((d) => d.day === todayDow)
      : data.weekly_timetable;

  async function acknowledgeNotice(id: string) {
    try {
      await api(`/api/v1/notices/${id}/read`, { method: "POST" });
      onRefresh?.();
    } catch (e) {
      console.error(e);
    }
  }

  async function generateLessonPlan() {
    const lp = data.lesson_plan;
    if (!lp) return;
    setLpBusy(true);
    try {
      await api("/api/v1/lesson-plans/generate", {
        method: "POST",
        body: JSON.stringify({
          class_id: lp.class_id,
          subject_id: lp.subject_id,
          topic: lp.topic,
          chapter: lp.chapter,
        }),
      });
      onRefresh?.();
    } catch (e) {
      console.error(e);
    } finally {
      setLpBusy(false);
    }
  }

  async function approveLessonPlan(id: string) {
    setLpBusy(true);
    try {
      await api(`/api/v1/lesson-plans/${id}/approve`, { method: "POST" });
      onRefresh?.();
    } catch (e) {
      console.error(e);
    } finally {
      setLpBusy(false);
    }
  }

  async function regenerateLessonPlan(id: string) {
    setLpBusy(true);
    try {
      await api(`/api/v1/lesson-plans/${id}/regenerate`, { method: "POST" });
      onRefresh?.();
    } catch (e) {
      console.error(e);
    } finally {
      setLpBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      {/* Header */}
      <div className="card bento-glass" style={{ padding: "24px 28px" }}>
        <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 6px" }}>{data.greeting}</h1>
        <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: 15 }}>{data.tagline}</p>
      </div>

      {/* Pending work strip */}
      {data.pending_work.length > 0 && (
        <div>
          <ZoneLabel title="Action needed" />
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {data.pending_work.map((p) => (
              <Link
                key={p.kind}
                href={p.href}
                className="card"
                style={{
                  flex: "1 1 220px",
                  padding: "14px 18px",
                  textDecoration: "none",
                  color: "inherit",
                  borderLeft: "4px solid var(--accent)",
                }}
              >
                <div style={{ fontWeight: 700, fontSize: 14 }}>{p.label}</div>
                {p.detail && <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{p.detail}</div>}
                <div style={{ fontSize: 22, fontWeight: 800, marginTop: 8, color: "var(--accent-dark)" }}>{p.count}</div>
              </Link>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 24 }}>
        {/* NOW */}
        <section>
          <ZoneLabel title="Now" subtitle="Today's classes" />
          {data.today_classes.length === 0 ? (
            <div className="card" style={{ padding: 24, color: "var(--text-muted)", fontSize: 14 }}>
              No classes on your timetable today. Check your weekly schedule below.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {data.today_classes.map((c) => {
                const att = attBadge(c.attendance_status);
                return (
                  <div key={c.slot_id} className="card" style={{ padding: 18 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                      <div>
                        <div style={{ fontSize: 13, color: "var(--accent-dark)", fontWeight: 700 }}>
                          <Clock size={14} style={{ display: "inline", verticalAlign: "-2px", marginRight: 6 }} />
                          {c.start_time} – {c.end_time}
                        </div>
                        <div style={{ fontSize: 18, fontWeight: 800, marginTop: 6 }}>
                          {c.class_label} · {c.subject_name}
                        </div>
                        {c.room && (
                          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                            <MapPin size={12} style={{ display: "inline", marginRight: 4 }} />Room {c.room}
                          </div>
                        )}
                      </div>
                      <span style={{
                        fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 999,
                        background: att.bg, color: att.color, whiteSpace: "nowrap",
                      }}>
                        {att.label}
                      </span>
                    </div>
                    {c.next_topic && (
                      <div style={{ fontSize: 13, marginTop: 12, color: "var(--text-secondary)" }}>
                        <BookOpen size={13} style={{ display: "inline", marginRight: 6 }} />
                        Focus topic: <strong>{c.next_topic}</strong>
                      </div>
                    )}
                    <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
                      {c.actions.map((a) => (
                        <Link
                          key={a.label}
                          href={a.href}
                          className={a.variant === "primary" ? "btn btn-primary" : "btn btn-outline"}
                          style={{ width: "auto", padding: "8px 14px", fontSize: 12 }}
                        >
                          {a.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* NEXT */}
        <section>
          <ZoneLabel title="Next" subtitle="Plan ahead" />
          {data.lesson_plan && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }} id="generate-lesson-plan">
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--accent-dark)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                <Sparkles size={13} style={{ display: "inline", marginRight: 4 }} />
                AI Lesson Plan · {data.lesson_plan.status === "draft" ? "Draft" : data.lesson_plan.status === "approved" ? "Approved" : "Preview"}
              </div>
              <div style={{ fontWeight: 800, fontSize: 17, marginTop: 8 }}>
                {data.lesson_plan.schedule_label}: {data.lesson_plan.class_label} {data.lesson_plan.subject_name}
              </div>
              {data.lesson_plan.topic && (
                <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 6 }}>
                  Chapter: {data.lesson_plan.chapter} · Topic: {data.lesson_plan.topic}
                </div>
              )}
              <ol style={{ margin: "14px 0 0", paddingLeft: 20, fontSize: 13, color: "var(--text-secondary)" }}>
                {data.lesson_plan.segments.map((s, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>{s.duration_min} min — {s.activity}</li>
                ))}
              </ol>
              <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
                {data.lesson_plan.status === "none" && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ width: "auto", padding: "8px 12px", fontSize: 12 }}
                    disabled={lpBusy}
                    onClick={generateLessonPlan}
                  >
                    <Sparkles size={13} /> {lpBusy ? "Generating…" : "Generate"}
                  </button>
                )}
                {data.lesson_plan.id && data.lesson_plan.can_approve && data.lesson_plan.status === "draft" && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ width: "auto", padding: "8px 12px", fontSize: 12, background: "var(--success)" }}
                    disabled={lpBusy}
                    onClick={() => approveLessonPlan(data.lesson_plan!.id!)}
                  >
                    <CheckCircle2 size={13} /> Approve
                  </button>
                )}
                {data.lesson_plan.id && (
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ width: "auto", padding: "8px 12px", fontSize: 12 }}
                    disabled={lpBusy}
                    onClick={() => regenerateLessonPlan(data.lesson_plan!.id!)}
                  >
                    <RefreshCw size={13} /> Regenerate
                  </button>
                )}
                {data.lesson_plan.actions.map((a) => (
                  <Link key={a.label} href={a.href} className="btn btn-outline" style={{ width: "auto", padding: "8px 12px", fontSize: 12 }}>
                    {a.label}
                  </Link>
                ))}
              </div>
            </div>
          )}

          <div className="card" style={{ padding: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                <CalendarDays size={18} /> My week
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                {(["today", "week"] as const).map((f) => (
                  <button
                    key={f}
                    type="button"
                    className={ttFilter === f ? "btn btn-primary" : "btn btn-outline"}
                    style={{ width: "auto", padding: "4px 10px", fontSize: 11 }}
                    onClick={() => setTtFilter(f)}
                  >
                    {f === "today" ? "Today" : "Week"}
                  </button>
                ))}
              </div>
            </div>
            {filteredTt.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>No timetable slots for this view.</p>
            ) : (
              filteredTt.map((d) => (
                <div key={d.day} style={{ marginBottom: 12 }}>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>{d.day_label}</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                    {d.slots.map((s, i) => (
                      <span key={i}>
                        {i > 0 && " · "}
                        {s.start_time} {s.class_label} {s.subject_name}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
            <Link href="/dashboard/timetable" style={{ fontSize: 13, color: "var(--accent-dark)", display: "inline-flex", alignItems: "center", gap: 4, marginTop: 8 }}>
              Full timetable <ChevronRight size={14} />
            </Link>
          </div>
        </section>
      </div>

      {/* WATCHLIST */}
      <section>
        <ZoneLabel title="Watchlist" subtitle="My students' progress — your subjects only" />
        {data.subject_progress.length === 0 ? (
          <div className="card" style={{ padding: 24, color: "var(--text-muted)", fontSize: 14 }}>
            Mastery data will appear after exams with topic tags are entered for your classes.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
            {data.subject_progress.map((p) => (
              <div key={`${p.class_id}-${p.subject_id}`} className="card" style={{ padding: 18 }}>
                <div style={{ fontWeight: 800, fontSize: 16 }}>{p.class_label} · {p.subject_name}</div>
                {p.average_mastery != null ? (
                  <div style={{ fontSize: 28, fontWeight: 800, margin: "10px 0", color: p.average_mastery >= 60 ? "var(--success)" : "var(--warning)" }}>
                    {p.average_mastery}%<span style={{ fontSize: 13, fontWeight: 500, color: "var(--text-muted)", marginLeft: 8 }}>avg mastery</span>
                  </div>
                ) : (
                  <div style={{ fontSize: 13, color: "var(--text-muted)", margin: "10px 0" }}>No mastery data yet</div>
                )}
                {p.weak_concepts.length > 0 && (
                  <div style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", marginBottom: 6 }}>Weak concepts</div>
                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                      {p.weak_concepts.map((w) => <li key={w}>{w}</li>)}
                    </ul>
                  </div>
                )}
                {p.students_needing_attention.length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", marginBottom: 6 }}>
                      <AlertCircle size={12} style={{ display: "inline", marginRight: 4 }} />
                      Needs attention
                    </div>
                    <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", fontSize: 13 }}>
                      {p.students_needing_attention.map((s) => (
                        <li key={s.student_id} style={{ marginBottom: 6, padding: "6px 8px", background: "var(--bg)", borderRadius: 6 }}>
                          <strong>{s.student_name}</strong>: {s.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <Link
                  href={`/dashboard/mastery`}
                  style={{ fontSize: 12, color: "var(--accent-dark)", marginTop: 12, display: "inline-block" }}
                >
                  Review flags →
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Notices */}
      {(data.staff_notices.length > 0 || data.school_notices.length > 0) && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
          {data.staff_notices.length > 0 && (
            <div className="card" style={{ padding: 18 }}>
              <div style={{ fontWeight: 700, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <Megaphone size={17} /> Staff notices
              </div>
              {data.staff_notices.map((n) => (
                <div key={n.id} style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 12 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{n.title}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{n.content}</div>
                  {n.can_acknowledge && !n.acknowledged && (
                    <button
                      className="btn btn-outline"
                      style={{ width: "auto", padding: "6px 12px", fontSize: 12, marginTop: 8 }}
                      onClick={() => acknowledgeNotice(n.id)}
                    >
                      <CheckCircle2 size={13} /> Acknowledge
                    </button>
                  )}
                  {n.acknowledged && (
                    <span style={{ fontSize: 11, color: "var(--success)", marginTop: 8, display: "inline-block" }}>Acknowledged</span>
                  )}
                </div>
              ))}
            </div>
          )}
          {data.school_notices.length > 0 && (
            <div className="card" style={{ padding: 18 }}>
              <div style={{ fontWeight: 700, marginBottom: 12 }}>School / parent notices</div>
              {data.school_notices.map((n) => (
                <div key={n.id} style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 12 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{n.title}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{n.content}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ZoneLabel({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--accent-dark)" }}>
        {title}
      </div>
      {subtitle && <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{subtitle}</div>}
    </div>
  );
}
