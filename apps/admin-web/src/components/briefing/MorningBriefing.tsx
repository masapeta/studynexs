"use client";

import Link from "next/link";
import {
  AlertCircle,
  CalendarDays,
  ClipboardCheck,
  Megaphone,
  Sparkles,
  Target,
  TrendingUp,
  UserPlus,
  Users,
  Wallet,
} from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { DashboardWidgets } from "./DashboardWidgets";
import { SchoolDayPanel } from "./SchoolDayPanel";
import { briefingDate, inr } from "@/lib/format";

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

function StatTile({
  label,
  value,
  icon: Icon,
  toneClass,
}: {
  label: string;
  value: React.ReactNode;
  icon: React.ElementType;
  toneClass: string;
}) {
  return (
    <div className="briefing-card briefing-stat">
      <div className="briefing-stat-head">
        <span className="briefing-stat-label">{label}</span>
        <Icon size={16} className={toneClass} />
      </div>
      <div className="briefing-stat-value">{value}</div>
    </div>
  );
}

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
  const spent = summary.expenses_this_month ?? 0;
  const notice = summary.notices?.[0];

  const qpPending = (summary.incharge_classes ?? []).reduce(
    (n, c) => n + (c.pending_qp_approvals || 0),
    0
  );
  const lowAttClasses = (summary.incharge_classes ?? []).filter(
    (c) => (c.attendance_percent ?? 100) < 85
  );

  const stats = isAdmin
    ? [
        {
          label: "Students enrolled",
          value: summary.total_students ?? 0,
          icon: Users,
          toneClass: "briefing-tone-ink",
        },
        {
          label: "Present today",
          value: `${att}%`,
          icon: ClipboardCheck,
          toneClass: "briefing-tone-sage",
        },
        {
          label: "Fees collected",
          value: inr(collected),
          icon: Wallet,
          toneClass: "briefing-tone-sage",
        },
        {
          label: "In admissions pipeline",
          value: pipeline,
          icon: UserPlus,
          toneClass: "briefing-tone-brass",
        },
      ]
    : [
        {
          label: "Your classes",
          value: summary.incharge_classes?.length ?? 0,
          icon: Users,
          toneClass: "briefing-tone-ink",
        },
        {
          label: "Papers to approve",
          value: qpPending,
          icon: Sparkles,
          toneClass: "briefing-tone-brass",
        },
        {
          label: "Events this term",
          value: eventsCount,
          icon: ClipboardCheck,
          toneClass: "briefing-tone-sage",
        },
        {
          label: "Quick link",
          value: "Mastery",
          icon: Target,
          toneClass: "briefing-tone-blue",
        },
      ];

  return (
    <div className="briefing-page">
      <header className="briefing-header">
        <div>
          <p className="briefing-eyebrow">{briefingDate()} · morning briefing</p>
          <h1 className="briefing-title">Good morning, {first}</h1>
          <p className="briefing-subtitle">{summary.subtitle}</p>
        </div>
      </header>

      <div className="briefing-stat-grid">
        {stats.map((s) => (
          <StatTile key={s.label} {...s} />
        ))}
      </div>

      <div className="briefing-main-grid">
        <SchoolDayPanel
          defaultClassId={
            summary.incharge_classes?.[0]?.class_id ??
            null
          }
        />

        <div className="briefing-side-stack">
          <div className="briefing-card briefing-panel">
            <div className="briefing-panel-head">
              <AlertCircle size={16} className="briefing-tone-coral" />
              <h3>Needs your attention</h3>
            </div>
            <div className="briefing-attention-grid">
              {isAdmin && att < 90 && (
                <Link href="/dashboard/attendance" className="briefing-attention briefing-attention-coral">
                  <span className="briefing-attention-kicker">Attendance below 90%</span>
                  <span className="briefing-attention-body">{att}% present school-wide today</span>
                </Link>
              )}
              {pendingFees > 0 && (
                <Link href="/dashboard/fees" className="briefing-attention briefing-attention-brass">
                  <span className="briefing-attention-kicker">Fees outstanding</span>
                  <span className="briefing-attention-body">{inr(pendingFees)} pending collection</span>
                </Link>
              )}
              {pipeline > 0 && (
                <Link href="/dashboard/admissions" className="briefing-attention briefing-attention-neutral">
                  <span className="briefing-attention-kicker">Admissions pipeline</span>
                  <span className="briefing-attention-body">{pipeline} candidates in progress</span>
                </Link>
              )}
              {qpPending > 0 && (
                <Link href="/dashboard/ai-papers" className="briefing-attention briefing-attention-brass">
                  <span className="briefing-attention-kicker">{qpPending} papers awaiting approval</span>
                  <span className="briefing-attention-body">Review AI question papers from your teachers</span>
                </Link>
              )}
              {!isAdmin && lowAttClasses.length > 0 && (
                <Link href="/dashboard/attendance" className="briefing-attention briefing-attention-coral">
                  <span className="briefing-attention-kicker">Low attendance in class</span>
                  <span className="briefing-attention-body">
                    {lowAttClasses.map((c) => c.class_label).join(", ")}
                  </span>
                </Link>
              )}
              <Link href="/dashboard/mastery" className="briefing-attention briefing-attention-neutral">
                <span className="briefing-attention-kicker">Topic mastery</span>
                <span className="briefing-attention-body">Review weakness flags and parent notes</span>
              </Link>
              <Link href="/dashboard/exams/corrections" className="briefing-attention briefing-attention-neutral">
                <span className="briefing-attention-kicker">Exam loop</span>
                <span className="briefing-attention-body">Answer-sheet corrections and AI grading history</span>
              </Link>
              {pendingFees === 0 && att >= 90 && qpPending === 0 && isAdmin && (
                <p className="briefing-muted-text">All clear for now — great start to the day.</p>
              )}
            </div>
          </div>

          {isAdmin && (
            <div className="briefing-card briefing-panel">
              <div className="briefing-panel-head">
                <h3>Finance snapshot</h3>
                <TrendingUp size={16} className="briefing-tone-sage" />
              </div>
              <div className="briefing-finance-row">
                <div>
                  <div className="briefing-finance-value briefing-tone-sage">{inr(collected)}</div>
                  <div className="briefing-finance-label">collected</div>
                </div>
                <div>
                  <div className="briefing-finance-value briefing-tone-coral">{inr(spent)}</div>
                  <div className="briefing-finance-label">spent</div>
                </div>
                <div>
                  <div className="briefing-finance-value briefing-tone-ink">
                    {inr(Math.max(0, collected - spent))}
                  </div>
                  <div className="briefing-finance-label">net</div>
                </div>
              </div>
            </div>
          )}

          {notice && (
            <div className="briefing-card briefing-panel">
              <div className="briefing-panel-head">
                <Megaphone size={16} className="briefing-tone-brass" />
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
            <div className="briefing-card briefing-panel">
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
      </div>

      {isAdmin && <DashboardWidgets userId={userId} isAdmin={isAdmin} />}
    </div>
  );
}
