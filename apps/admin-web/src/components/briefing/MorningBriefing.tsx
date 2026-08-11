"use client";

import Link from "next/link";
import { CheckCircle2, ChevronRight, Megaphone } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { CountUp } from "./CountUp";
import { Sparkline } from "./Sparkline";
import { DashboardWidgets } from "./DashboardWidgets";
import { DashboardAnalytics } from "./DashboardAnalytics";
import { SchoolDayPanel } from "./SchoolDayPanel";
import { inr, noticeAudienceLabel } from "@/lib/format";
import { FINANCE, STUDENTS, TEACHING } from "@/lib/dashboard-routes";

export type { TimetablePeriod } from "./SchoolDayPanel";

export type SchoolAttendanceStatus =
  | "not_recorded"
  | "in_progress"
  | "attention_needed"
  | "healthy";

export type BriefingSummary = {
  persona: "admin" | "class_incharge" | "teacher";
  subtitle: string;
  total_students?: number | null;
  total_teachers?: number | null;
  total_classes?: number | null;
  pending_fees?: number | null;
  pending_qp_approvals?: number | null;
  school_attendance_status?: SchoolAttendanceStatus | null;
  school_attendance_percent?: number | null;
  attendance_marked_today?: number | null;
  attendance_enrolled?: number | null;
  incharge_classes?: {
    class_id: string;
    class_label: string;
    attendance_percent?: number | null;
    pending_qp_approvals: number;
  }[];
  attendance_trend?: number[];
  admissions_pipeline?: number | null;
  expenses_this_month?: number | null;
  class_performance?: {
    label: string;
    present?: number;
    strength?: number;
    percentage: number;
    date?: string;
  }[];
  notices?: {
    id: string;
    title: string;
    content: string;
    audience: string;
    priority: string;
    created_at?: string;
  }[];
  principal_interventions?: {
    id: string;
    severity: "high" | "medium";
    issue: string;
    why_it_matters: string;
    affected_scope: string;
    owner: string;
    recommended_intervention: string;
    status: string;
    href: string;
    evidence_chain_href: string;
    evidence: {
      label: string;
      value: string;
      href?: string | null;
    }[];
  }[];
};

export type FeeStats = {
  total_collected?: number;
  pending_amount?: number;
  pending_families?: number;
};

type Props = {
  userName: string;
  userId: string;
  summary: BriefingSummary;
  feeStats?: FeeStats | null;
  eventsCount?: number;
};

type KpiItem = {
  label: string;
  value: React.ReactNode;
  hint?: string;
  hintWarn?: boolean;
  tone?: "accent" | "sage" | "brass" | "neutral";
  /** Optional trend series (oldest first) rendered as a mini sparkline. */
  trend?: number[];
};

type PriorityAlert = {
  priority: number;
  href: string;
  kicker: string;
  body: string;
  action: string;
  tone: "coral" | "brass" | "neutral";
};

const KPI_SPARK_STROKE: Record<string, string> = {
  accent: "var(--accent)",
  sage: "#34d399",
  brass: "#f59e0b",
  neutral: "#94a3b8",
};

function ExecutiveKpiBar({ items }: { items: KpiItem[] }) {
  return (
    <div className="briefing-exec-row briefing-exec-row--kpis" role="list">
      {items.map((item, index) => (
        <div
          key={item.label}
          className={`briefing-glass-chip briefing-exec-kpi briefing-exec-kpi--${item.tone ?? "neutral"}`}
          role="listitem"
          style={{ ["--kpi-index" as string]: index }}
        >
          <span className="briefing-exec-kpi-label">{item.label}</span>
          <span className="briefing-exec-kpi-value">{item.value}</span>
          {item.hint ? (
            <span
              className={`briefing-exec-kpi-hint${item.hintWarn ? " briefing-exec-kpi-hint--warn" : ""}`}
            >
              {item.hint}
            </span>
          ) : null}
          {item.trend && item.trend.length >= 2 ? (
            <Sparkline
              data={item.trend}
              stroke={KPI_SPARK_STROKE[item.tone ?? "neutral"]}
            />
          ) : null}
        </div>
      ))}
    </div>
  );
}

const QUICK_LINKS = [
  { label: "Curriculum", href: TEACHING.curriculum },
  { label: "AI papers", href: TEACHING.aiPapers },
  { label: "AI marking", href: TEACHING.corrections },
  { label: "Mastery", href: TEACHING.mastery },
] as const;

export function MorningBriefing({
  userName,
  userId,
  summary,
  feeStats,
  eventsCount = 0,
}: Props) {
  const first = userName.split(" ")[0] || "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const isAdmin = summary.persona === "admin";
  const attStatus = summary.school_attendance_status ?? "not_recorded";
  const att =
    summary.school_attendance_percent != null ? summary.school_attendance_percent : null;
  const markedToday = summary.attendance_marked_today ?? 0;
  const enrolledToday = summary.attendance_enrolled ?? summary.total_students ?? 0;
  const pendingFees = summary.pending_fees ?? feeStats?.pending_amount ?? 0;
  const collected = feeStats?.total_collected ?? 0;
  const pipeline = summary.admissions_pipeline ?? 0;
  const notice = summary.notices?.[0];
  const collectionRate =
    collected + pendingFees > 0 ? Math.round((collected / (collected + pendingFees)) * 100) : 0;

  const qpPending =
    summary.pending_qp_approvals ??
    (summary.incharge_classes ?? []).reduce(
      (n, c) => n + (c.pending_qp_approvals || 0),
      0
    );
  const principalInterventions = summary.principal_interventions ?? [];
  const lowAttClasses = (summary.incharge_classes ?? []).filter(
    (c) => (c.attendance_percent ?? 100) < 85
  );

  const adminKpis: KpiItem[] = [
    {
      label: "Students",
      value: <CountUp value={summary.total_students ?? 0} />,
      tone: "accent",
    },
    (() => {
      if (attStatus === "not_recorded") {
        return {
          label: "Present today",
          value: "—",
          hint: "Not recorded yet",
          tone: "neutral" as const,
          trend: summary.attendance_trend,
        };
      }
      if (attStatus === "in_progress") {
        return {
          label: "Present today",
          value: att != null ? <CountUp value={att} format={(n) => `${Math.round(n)}%`} /> : "—",
          hint: `Roll in progress · ${markedToday}/${enrolledToday} marked`,
          tone: "brass" as const,
          trend: summary.attendance_trend,
        };
      }
      if (attStatus === "attention_needed") {
        return {
          label: "Present today",
          value: att != null ? <CountUp value={att} format={(n) => `${Math.round(n)}%`} /> : "—",
          hint: "Below target",
          hintWarn: true,
          tone: "brass" as const,
          trend: summary.attendance_trend,
        };
      }
      return {
        label: "Present today",
        value: att != null ? <CountUp value={att} format={(n) => `${Math.round(n)}%`} /> : "—",
        hint: "On track",
        tone: "sage" as const,
        trend: summary.attendance_trend,
      };
    })(),
    {
      label: "Fees collected",
      value: <CountUp value={collected} format={(n) => inr(Math.round(n))} />,
      hint: collectionRate > 0 ? `${collectionRate}% of target` : undefined,
      tone: "sage",
    },
    {
      label: "Admissions",
      value: <CountUp value={pipeline} />,
      hint: pipeline > 0 ? "In pipeline" : undefined,
      tone: "accent",
    },
  ];

  const inchargeKpis: KpiItem[] = [
    {
      label: "Your classes",
      value: <CountUp value={summary.incharge_classes?.length ?? 0} />,
      tone: "accent",
    },
    {
      label: "Papers to approve",
      value: <CountUp value={qpPending} />,
      tone: qpPending > 0 ? "brass" : "sage",
    },
    { label: "Events this term", value: <CountUp value={eventsCount} />, tone: "accent" },
    { label: "Quick link", value: "Mastery", tone: "neutral" },
  ];

  const priorityAlerts: PriorityAlert[] = [];

  if (isAdmin && attStatus === "attention_needed" && att != null) {
    priorityAlerts.push({
      priority: 1,
      href: "/dashboard/attendance",
      kicker: "Attendance below 90%",
      body: `${att}% present school-wide today`,
      action: "Review attendance",
      tone: "coral",
    });
  }
  if (isAdmin && attStatus === "not_recorded") {
    priorityAlerts.push({
      priority: 3,
      href: "/dashboard/attendance",
      kicker: "Attendance not recorded",
      body: "Today’s rolls have not been marked yet",
      action: "Mark attendance",
      tone: "neutral",
    });
  }
  if (pendingFees > 0) {
    const familyHint =
      feeStats?.pending_families && feeStats.pending_families > 0
        ? ` across ${feeStats.pending_families} famil${feeStats.pending_families === 1 ? "y" : "ies"}`
        : "";
    priorityAlerts.push({
      priority: 2,
      href: FINANCE.fees,
      kicker: "Fees outstanding",
      body: `${inr(pendingFees)} pending${familyHint}`,
      action: "Open fee follow-up",
      tone: "brass",
    });
  }
  if (qpPending > 0) {
    priorityAlerts.push({
      priority: 2,
      href: TEACHING.aiPapers,
      kicker: `${qpPending} paper${qpPending === 1 ? "" : "s"} awaiting approval`,
      body: "Teachers are waiting on your review before exams can proceed",
      action: "Approve papers",
      tone: "brass",
    });
  }
  if (pipeline > 0) {
    priorityAlerts.push({
      priority: 3,
      href: STUDENTS.admissions,
      kicker: "Admissions pipeline",
      body: `${pipeline} candidate${pipeline === 1 ? "" : "s"} in progress`,
      action: "Review admissions",
      tone: "neutral",
    });
  }
  if (!isAdmin && lowAttClasses.length > 0) {
    priorityAlerts.push({
      priority: 1,
      href: "/dashboard/attendance",
      kicker: "Low attendance in class",
      body: lowAttClasses.map((c) => c.class_label).join(", "),
      action: "Review attendance",
      tone: "coral",
    });
  }

  priorityAlerts.sort((a, b) => a.priority - b.priority);
  const topAlerts = priorityAlerts.slice(0, 4);
  const allClear =
    isAdmin &&
    priorityAlerts.length === 0 &&
    attStatus === "healthy" &&
    pendingFees === 0 &&
    qpPending === 0;

  const storyLine = isAdmin
    ? (() => {
        if (allClear) {
          return `${att}% present school-wide · operations look healthy today`;
        }
        if (attStatus === "not_recorded") {
          return topAlerts.length <= 1
            ? "Attendance has not been recorded yet · mark today's rolls to begin"
            : `Attendance has not been recorded yet · ${topAlerts.length} items need your attention`;
        }
        if (attStatus === "in_progress") {
          return `Roll call in progress (${markedToday}/${enrolledToday} marked) · ${topAlerts.length} item${topAlerts.length === 1 ? "" : "s"} need your attention`;
        }
        return `${att ?? "—"}% present school-wide · ${topAlerts.length} item${topAlerts.length === 1 ? "" : "s"} need your attention`;
      })()
    : summary.subtitle;

  return (
    <div className="briefing-page briefing-page--executive">
      <header className="briefing-header briefing-exec-header">
        <h1 className="briefing-title">{greeting}, {first}</h1>
        <p className="briefing-subtitle">{summary.subtitle}</p>
        {isAdmin ? <p className="briefing-exec-story">{storyLine}</p> : null}
      </header>

      <ExecutiveKpiBar items={isAdmin ? adminKpis : inchargeKpis} />

      <div className="briefing-exec-row briefing-exec-row--command">
        <SchoolDayPanel
          defaultClassId={summary.incharge_classes?.[0]?.class_id ?? null}
        />

        <div className="briefing-glass-chip briefing-card briefing-panel briefing-exec-priority">
          <div className="briefing-panel-head">
            <h3>What needs attention</h3>
            {priorityAlerts.length > 4 && (
              <Link href="/dashboard/attendance" className="briefing-link briefing-panel-action">
                View all
              </Link>
            )}
          </div>

          {allClear ? (
            <p className="briefing-exec-all-clear">All clear — school operations look healthy today.</p>
          ) : topAlerts.length === 0 ? (
            <div className="briefing-exec-empty-state briefing-exec-empty-state--compact">
              <CheckCircle2 size={18} className="briefing-exec-empty-state__icon" aria-hidden />
              <p className="briefing-exec-empty-state__title">All caught up</p>
              <span className="briefing-exec-empty-state__hint">
                Nothing needs your attention right now — new approvals, attendance gaps,
                and fee follow-ups will appear here.
              </span>
            </div>
          ) : (
            <div className="briefing-exec-priority-list">
              {topAlerts.map((alert, index) => (
                <Link
                  key={alert.kicker}
                  href={alert.href}
                  className={`briefing-exec-priority-item briefing-exec-priority-item--${alert.tone}${
                    index === 0 ? " briefing-exec-priority-item--primary" : ""
                  }`}
                >
                  <span className="briefing-exec-priority-dot" aria-hidden />
                  <div className="briefing-exec-priority-copy">
                    <strong>{alert.kicker}</strong>
                    <span>{alert.body}</span>
                  </div>
                  <span className="briefing-exec-priority-action">
                    {alert.action}
                    <ChevronRight size={14} aria-hidden />
                  </span>
                </Link>
              ))}
            </div>
          )}

          {isAdmin && (
            <div className="briefing-exec-quicklinks" aria-label="Quick links">
              {QUICK_LINKS.map((link) => (
                <Link key={link.href} href={link.href} className="briefing-exec-quicklink">
                  {link.label}
                </Link>
              ))}
            </div>
          )}
        </div>

        {notice && (
          <div className="briefing-glass-chip briefing-card briefing-panel briefing-panel--notice briefing-exec-notice">
            <div className="briefing-panel-head">
              <Megaphone size={15} className="briefing-tone-brass" aria-hidden />
              <h3>Latest notice</h3>
              <Link href="/dashboard/notices" className="briefing-link briefing-panel-action">
                View all
              </Link>
            </div>
            <p className="briefing-notice-title">{notice.title}</p>
            <p className="briefing-notice-body">{notice.content}</p>
            <div className="briefing-notice-meta">
              <StatusBadge tone="brass">{noticeAudienceLabel(notice.audience)}</StatusBadge>
              {(notice.priority === "high" || notice.priority === "urgent") && (
                <StatusBadge tone="red">{notice.priority}</StatusBadge>
              )}
            </div>
          </div>
        )}
      </div>

      {!isAdmin && (summary.incharge_classes?.length ?? 0) > 0 && (
        <div className="briefing-exec-row briefing-exec-row--classes">
          <div className="briefing-glass-chip briefing-card briefing-panel briefing-exec-classes">
            <div className="briefing-panel-head">
              <h3>Your classes today</h3>
            </div>
            <div className="briefing-class-list">
              {summary.incharge_classes!.map((c) => (
                <div key={c.class_id} className="briefing-class-row">
                  <span className="briefing-class-name">{c.class_label}</span>
                  <span className="briefing-class-stat">
                    {c.attendance_percent != null
                      ? `${c.attendance_percent}% present`
                      : "Attendance not recorded"}
                  </span>
                  {c.pending_qp_approvals > 0 && (
                    <StatusBadge tone="brass">{c.pending_qp_approvals} QP</StatusBadge>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {isAdmin && (
        <section
          className="briefing-glass-chip briefing-card briefing-panel"
          data-testid="principal-intervention-center"
          aria-labelledby="principal-intervention-title"
          style={{ marginTop: 14 }}
        >
          <div className="briefing-panel-head">
            <div>
              <h3 id="principal-intervention-title">Intervention Center</h3>
              <p className="briefing-muted-text" style={{ margin: "4px 0 0" }}>
                Evidence-backed priorities for human follow-up — not a reporting dashboard.
              </p>
            </div>
            <Link href={TEACHING.mastery} className="briefing-link briefing-panel-action">
              Open mastery
            </Link>
          </div>

          {principalInterventions.length === 0 ? (
            <p className="briefing-exec-all-clear" data-testid="principal-intervention-empty">
              No evidence-backed academic interventions right now.
            </p>
          ) : (
            <div
              className="briefing-exec-priority-list"
              data-testid="principal-intervention-list"
            >
              {principalInterventions.map((item, index) => (
                <Link
                  key={item.id}
                  href={item.href}
                  data-testid="principal-intervention-card"
                  className={`briefing-exec-priority-item briefing-exec-priority-item--${
                    item.severity === "high" ? "coral" : "brass"
                  }${index === 0 ? " briefing-exec-priority-item--primary" : ""}`}
                  style={{ alignItems: "flex-start" }}
                >
                  <span className="briefing-exec-priority-dot" aria-hidden />
                  <div className="briefing-exec-priority-copy" style={{ gap: 6 }}>
                    <strong>{item.issue}</strong>
                    <span>{item.why_it_matters}</span>
                    <span>
                      <b>Owner:</b> {item.owner}
                    </span>
                    <span>
                      <b>Recommended human intervention:</b>{" "}
                      {item.recommended_intervention}
                    </span>
                    {item.evidence.length > 0 && (
                      <span>
                        <b>Evidence:</b>{" "}
                        {item.evidence
                          .slice(0, 4)
                          .map((e) => `${e.label}: ${e.value}`)
                          .join(" · ")}
                      </span>
                    )}
                  </div>
                  <span className="briefing-exec-priority-action">
                    Review evidence
                    <ChevronRight size={14} aria-hidden />
                  </span>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {isAdmin && (
        <DashboardAnalytics
          classPerformance={summary.class_performance}
          feeStats={feeStats}
          attendanceStatus={attStatus}
        />
      )}
      {isAdmin && <DashboardWidgets userId={userId} isAdmin={isAdmin} layout="executive" />}
    </div>
  );
}
