"use client";

import Link from "next/link";
import { ChevronRight, Megaphone } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { DashboardWidgets } from "./DashboardWidgets";
import { DashboardAnalytics } from "./DashboardAnalytics";
import { SchoolDayPanel } from "./SchoolDayPanel";
import { inr } from "@/lib/format";
import { FINANCE, STUDENTS, TEACHING } from "@/lib/dashboard-routes";

export type { TimetablePeriod } from "./SchoolDayPanel";

export type BriefingSummary = {
  persona: "admin" | "class_incharge" | "teacher";
  subtitle: string;
  total_students?: number | null;
  total_teachers?: number | null;
  total_classes?: number | null;
  pending_fees?: number | null;
  school_attendance_percent?: number | null;
  incharge_classes?: {
    class_id: string;
    class_label: string;
    attendance_percent?: number | null;
    pending_qp_approvals: number;
  }[];
  admissions_pipeline?: number | null;
  expenses_this_month?: number | null;
  class_performance?: { label: string; percentage: number }[];
  notices?: {
    id: string;
    title: string;
    content: string;
    audience: string;
    priority: string;
    created_at?: string;
  }[];
};

export type FeeStats = {
  total_collected?: number;
  pending_amount?: number;
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
};

type PriorityAlert = {
  priority: number;
  href: string;
  kicker: string;
  body: string;
  tone: "coral" | "brass" | "neutral";
};

function ExecutiveKpiBar({ items }: { items: KpiItem[] }) {
  return (
    <div className="briefing-exec-row briefing-exec-row--kpis" role="list">
      {items.map((item) => (
        <div key={item.label} className="briefing-glass-chip briefing-exec-kpi" role="listitem">
          <span className="briefing-exec-kpi-label">{item.label}</span>
          <span className="briefing-exec-kpi-value">{item.value}</span>
          {item.hint ? (
            <span
              className={`briefing-exec-kpi-hint${item.hintWarn ? " briefing-exec-kpi-hint--warn" : ""}`}
            >
              {item.hint}
            </span>
          ) : null}
        </div>
      ))}
    </div>
  );
}

const QUICK_LINKS = [
  { label: "Mastery", href: TEACHING.mastery },
  { label: "Exam loop", href: TEACHING.corrections },
  { label: "Attendance", href: "/dashboard/attendance" },
  { label: "Timetable", href: "/dashboard/timetable" },
] as const;

export function MorningBriefing({
  userName,
  userId,
  summary,
  feeStats,
  eventsCount = 0,
}: Props) {
  const first = userName.split(" ")[0] || "there";
  const isAdmin = summary.persona === "admin";
  const att = summary.school_attendance_percent ?? 0;
  const pendingFees = summary.pending_fees ?? feeStats?.pending_amount ?? 0;
  const collected = feeStats?.total_collected ?? 0;
  const pipeline = summary.admissions_pipeline ?? 0;
  const notice = summary.notices?.[0];
  const collectionRate =
    collected + pendingFees > 0 ? Math.round((collected / (collected + pendingFees)) * 100) : 0;

  const qpPending = (summary.incharge_classes ?? []).reduce(
    (n, c) => n + (c.pending_qp_approvals || 0),
    0
  );
  const lowAttClasses = (summary.incharge_classes ?? []).filter(
    (c) => (c.attendance_percent ?? 100) < 85
  );

  const adminKpis: KpiItem[] = [
    { label: "Students", value: summary.total_students ?? 0 },
    {
      label: "Present today",
      value: `${att}%`,
      hint: att < 90 ? "Below target" : undefined,
      hintWarn: att < 90,
    },
    {
      label: "Fees collected",
      value: inr(collected),
      hint: collectionRate > 0 ? `${collectionRate}% of target` : undefined,
    },
    { label: "Admissions", value: pipeline, hint: pipeline > 0 ? "In pipeline" : undefined },
  ];

  const inchargeKpis: KpiItem[] = [
    { label: "Your classes", value: summary.incharge_classes?.length ?? 0 },
    { label: "Papers to approve", value: qpPending },
    { label: "Events this term", value: eventsCount },
    { label: "Quick link", value: "Mastery" },
  ];

  const priorityAlerts: PriorityAlert[] = [];

  if (isAdmin && att < 90) {
    priorityAlerts.push({
      priority: 1,
      href: "/dashboard/attendance",
      kicker: "Attendance below 90%",
      body: `${att}% present school-wide today`,
      tone: "coral",
    });
  }
  if (pendingFees > 0) {
    priorityAlerts.push({
      priority: 2,
      href: FINANCE.fees,
      kicker: "Fees outstanding",
      body: `${inr(pendingFees)} pending collection`,
      tone: "brass",
    });
  }
  if (pipeline > 0) {
    priorityAlerts.push({
      priority: 3,
      href: STUDENTS.admissions,
      kicker: "Admissions pipeline",
      body: `${pipeline} candidates in progress`,
      tone: "neutral",
    });
  }
  if (qpPending > 0) {
    priorityAlerts.push({
      priority: 2,
      href: TEACHING.aiPapers,
      kicker: `${qpPending} papers awaiting approval`,
      body: "Review AI question papers from your teachers",
      tone: "brass",
    });
  }
  if (!isAdmin && lowAttClasses.length > 0) {
    priorityAlerts.push({
      priority: 1,
      href: "/dashboard/attendance",
      kicker: "Low attendance in class",
      body: lowAttClasses.map((c) => c.class_label).join(", "),
      tone: "coral",
    });
  }

  priorityAlerts.sort((a, b) => a.priority - b.priority);
  const topAlerts = priorityAlerts.slice(0, 4);
  const allClear =
    isAdmin && priorityAlerts.length === 0 && att >= 90 && pendingFees === 0 && qpPending === 0;

  return (
    <div className="briefing-page briefing-page--executive">
      <header className="briefing-header briefing-exec-header">
        <h1 className="briefing-title">Good morning, {first}</h1>
        <p className="briefing-subtitle">{summary.subtitle}</p>
      </header>

      <ExecutiveKpiBar items={isAdmin ? adminKpis : inchargeKpis} />

      <div className="briefing-exec-row briefing-exec-row--command">
        <SchoolDayPanel
          defaultClassId={summary.incharge_classes?.[0]?.class_id ?? null}
        />

        <div className="briefing-glass-chip briefing-card briefing-panel briefing-exec-priority">
          <div className="briefing-panel-head">
            <h3>Priority queue</h3>
            {priorityAlerts.length > 4 && (
              <Link href="/dashboard/attendance" className="briefing-link briefing-panel-action">
                View all
              </Link>
            )}
          </div>

          {allClear ? (
            <p className="briefing-exec-all-clear">All clear — school operations look healthy today.</p>
          ) : topAlerts.length === 0 ? (
            <p className="briefing-muted-text">No urgent items right now.</p>
          ) : (
            <div className="briefing-exec-priority-list">
              {topAlerts.map((alert) => (
                <Link
                  key={alert.kicker}
                  href={alert.href}
                  className={`briefing-exec-priority-item briefing-exec-priority-item--${alert.tone}`}
                >
                  <span className="briefing-exec-priority-dot" aria-hidden />
                  <div className="briefing-exec-priority-copy">
                    <strong>{alert.kicker}</strong>
                    <span>{alert.body}</span>
                  </div>
                  <ChevronRight size={14} className="briefing-exec-priority-chevron" aria-hidden />
                </Link>
              ))}
            </div>
          )}

          <div className="briefing-exec-quicklinks" aria-label="Quick links">
            {isAdmin &&
              QUICK_LINKS.map((link) => (
                <Link key={link.href} href={link.href} className="briefing-exec-quicklink">
                  {link.label}
                </Link>
              ))}
          </div>
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
              <StatusBadge tone="brass">{notice.audience}</StatusBadge>
              {(notice.priority === "high" || notice.priority === "urgent") && (
                <StatusBadge tone="red">{notice.priority}</StatusBadge>
              )}
            </div>
          </div>
        )}

        {!isAdmin && (summary.incharge_classes?.length ?? 0) > 0 && (
          <div className="briefing-glass-chip briefing-card briefing-panel briefing-exec-classes">
            <div className="briefing-panel-head">
              <h3>Your classes today</h3>
            </div>
            <div className="briefing-class-list">
              {summary.incharge_classes!.map((c) => (
                <div key={c.class_id} className="briefing-class-row">
                  <span className="briefing-class-name">{c.class_label}</span>
                  <span className="briefing-class-stat">
                    {c.attendance_percent ?? "—"}% present
                  </span>
                  {c.pending_qp_approvals > 0 && (
                    <StatusBadge tone="brass">{c.pending_qp_approvals} QP</StatusBadge>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {isAdmin && (
        <DashboardAnalytics
          classPerformance={summary.class_performance}
          feeStats={feeStats}
        />
      )}
      {isAdmin && <DashboardWidgets userId={userId} isAdmin={isAdmin} layout="executive" />}
    </div>
  );
}
