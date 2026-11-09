"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays, ClipboardList, MessageSquare, School, UserPlus } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api, getApiErrorMessage } from "@/lib/api";
import { Card, EmptyState, SectionHeader, StatTile } from "@/components/ui/kit";
import { TeacherCommandCenter, type TeacherHome } from "@/components/TeacherCommandCenter";
import { MorningBriefing, type BriefingSummary, type FeeStats } from "@/components/briefing/MorningBriefing";
import { useAssistant } from "@/components/assistant/AssistantProvider";
import { WORKSPACE_PROMPTS, roleToWorkspaceRole } from "@/lib/workspace-actions";

type MyClass = { class_id: string; class_label: string; is_incharge: boolean; subjects: string[] };

type Summary = BriefingSummary & {
  teacher_home?: TeacherHome | null;
  my_classes?: MyClass[];
  upcoming_events?: number | null;
  quick_actions?: { label: string; href: string }[];
};

function HomeSkeleton() {
  return (
    <div className="briefing-page briefing-page--executive" role="status" aria-busy="true" aria-label="Loading home">
      <div className="briefing-exec-row briefing-exec-row--kpis">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="briefing-glass-chip briefing-exec-kpi platform-skeleton" style={{ minHeight: 68 }} />
        ))}
      </div>
    </div>
  );
}

/** Chat-first, not chat-only: a composer entry plus the persona's home. */
function AskBar() {
  const { user } = useAuth();
  const { send, base } = useAssistant();
  const prompts = WORKSPACE_PROMPTS[roleToWorkspaceRole(user?.role)].slice(0, 3);
  return (
    <Card>
      <div className="sn-home-ask">
        <MessageSquare size={18} aria-hidden />
        <strong>Ask StudyNexs</strong>
        <div className="sn-ws-chips" style={{ marginLeft: "auto" }}>
          {prompts.map((p) => (
            <Link key={p} href={`${base}/assistant`} className="sn-ws-chip" onClick={() => void send(p)}>
              {p}
            </Link>
          ))}
          <Link href={`${base}/assistant`} className="btn btn-primary gw-btn-sm">Open chat</Link>
        </div>
      </div>
    </Card>
  );
}

function MyClasses({ classes }: { classes: MyClass[] }) {
  return (
    <section id="my-classes" aria-labelledby="my-classes-h" style={{ scrollMarginTop: 80 }}>
      <SectionHeader title="My classes" />
      {classes.length === 0 ? (
        <EmptyState icon={School} title="No classes assigned yet"
                    message="Your principal assigns classes and subjects. They will appear here." />
      ) : (
        <div className="sn-home-classes">
          {classes.map((c) => (
            <Card key={c.class_id} href={`/dashboard/classes/${c.class_id}`}>
              <strong id={c.class_id === classes[0].class_id ? "my-classes-h" : undefined}>{c.class_label}</strong>
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                {[c.is_incharge ? "Class incharge" : null, c.subjects.join(", ") || null].filter(Boolean).join(" · ")}
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

export function RoleHome() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [feeStats, setFeeStats] = useState<FeeStats | null>(null);
  const [eventsCount, setEventsCount] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    const isAdmin = user?.role === "admin" || user?.role === "super_admin";
    const [s, ev, fees] = await Promise.all([
      api<{ data: Summary }>("/api/v1/dashboard/summary").then((r) => r.data),
      api<{ data: unknown[] }>("/api/v1/ops/events").then((r) => (r.data || []).length).catch(() => 0),
      isAdmin
        ? api<{ data: FeeStats }>("/api/v1/fees/stats").then((r) => r.data).catch(() => null)
        : Promise.resolve(null),
    ]);
    return { s, ev, fees };
  }, [user?.role]);

  const apply = useCallback(
    (p: Promise<{ s: Summary; ev: number; fees: FeeStats | null }>, alive: () => boolean) =>
      p
        .then(({ s, ev, fees }) => {
          if (!alive()) return;
          setSummary(s);
          setEventsCount(ev);
          setFeeStats(fees);
          setError("");
        })
        .catch((e) => alive() && setError(getApiErrorMessage(e, "Could not load your home.")))
        .finally(() => alive() && setLoading(false)),
    []
  );

  useEffect(() => {
    if (!user) return;
    let on = true;
    void apply(fetchAll(), () => on);
    return () => {
      on = false;
    };
  }, [user, fetchAll, apply]);

  const reload = useCallback(() => {
    setLoading(true);
    void apply(fetchAll(), () => true);
  }, [apply, fetchAll]);

  if (!user) return null;
  if (loading) return <HomeSkeleton />;
  if (error || !summary) {
    return (
      <div className="card platform-state--error" style={{ padding: 24 }} role="alert">
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Home unavailable</h2>
        <p style={{ marginBottom: 16 }}>{error || "No data."}</p>
        <button className="btn btn-primary" type="button" onClick={reload} style={{ width: "auto" }}>Retry</button>
      </div>
    );
  }

  const persona = summary.persona;
  return (
    <div className="sn-home platform-motion-briefing-enter">
      <AskBar />
      {persona === "admin" && (
        <MorningBriefing userName={user.full_name} userId={user.id} summary={summary}
                         feeStats={feeStats} eventsCount={eventsCount} />
      )}
      {persona === "operations" && (
        <>
          <div className="sn-home-tiles">
            <Link href="/dashboard/admissions" className="sn-home-tile-link">
              <StatTile icon={UserPlus} label="Admissions in progress" value={summary.admissions_pipeline ?? 0} />
            </Link>
            <Link href="/dashboard/events" className="sn-home-tile-link">
              <StatTile icon={CalendarDays} label="Upcoming events" value={summary.upcoming_events ?? 0} />
            </Link>
          </div>
          {(summary.notices ?? []).length === 0 ? (
            <EmptyState icon={ClipboardList} title="No new notices" message="School notices will appear here." />
          ) : (
            <>
              <SectionHeader title="Notices" />
              <Card>
                {(summary.notices ?? []).map((n) => (
                  <div key={n.id} style={{ padding: "6px 0" }}><strong>{n.title}</strong></div>
                ))}
              </Card>
            </>
          )}
        </>
      )}
      {(persona === "class_incharge" || persona === "teacher") && (
        <>
          <MyClasses classes={summary.my_classes ?? []} />
          {summary.teacher_home ? <TeacherCommandCenter data={summary.teacher_home} onRefresh={reload} /> : null}
          {persona === "class_incharge" && !summary.teacher_home ? (
            <MorningBriefing userName={user.full_name} userId={user.id} summary={summary} eventsCount={eventsCount} />
          ) : null}
        </>
      )}
    </div>
  );
}
