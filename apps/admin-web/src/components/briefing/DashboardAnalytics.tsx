"use client";

import Link from "next/link";
import { inr, inrCompact } from "@/lib/format";
import { FINANCE } from "@/lib/dashboard-routes";
import {
  ClassAttendanceChart,
  formatAttendanceDateRange,
  type ClassAttendanceBar,
} from "./ClassAttendanceChart";
import { FeeCollectionGauge } from "./FeeCollectionGauge";

type ClassPerformance = ClassAttendanceBar;

type FeeStats = {
  total_collected?: number;
  pending_amount?: number;
  pending_families?: number;
};

type Props = {
  classPerformance?: ClassPerformance[];
  feeStats?: FeeStats | null;
  attendanceStatus?: "not_recorded" | "in_progress" | "attention_needed" | "healthy";
};

/** School-wide analytics — uses dashboard data when provided (no extra fetch). */
export function DashboardAnalytics({
  classPerformance = [],
  feeStats,
  attendanceStatus = "not_recorded",
}: Props) {
  const collected = feeStats?.total_collected ?? 0;
  const pending = feeStats?.pending_amount ?? 0;
  const pendingFamilies = feeStats?.pending_families ?? 0;
  const collectionRate =
    collected + pending > 0 ? Math.round((collected / (collected + pending)) * 100) : 0;
  const attendanceDateLabel = formatAttendanceDateRange(
    classPerformance.map((row) => row.date)
  );

  return (
    <section className="briefing-exec-insights" aria-labelledby="briefing-analytics-title">
      <div className="briefing-exec-section-head">
        <h2 id="briefing-analytics-title">School health</h2>
        <p>Attendance snapshot and fee collection status</p>
      </div>

      <div className="briefing-exec-row briefing-exec-row--insights">
        <div className="briefing-glass-chip briefing-exec-insight-chip briefing-exec-insight-chip--attendance">
          <div className="briefing-exec-insight-chip__head">
            <h3>Class attendance</h3>
            {attendanceStatus === "not_recorded" ? (
              <span className="briefing-exec-insight-chip__meta">Today&apos;s rolls not recorded</span>
            ) : attendanceDateLabel ? (
              <span className="briefing-exec-insight-chip__meta">
                {attendanceDateLabel === "Today"
                  ? "Today’s rolls"
                  : `Rolls for ${attendanceDateLabel}`}
              </span>
            ) : (
              <span className="briefing-exec-insight-chip__meta">Today&apos;s rolls</span>
            )}
          </div>
          <ClassAttendanceChart data={classPerformance} />
        </div>

        <div className="briefing-glass-chip briefing-exec-insight-chip briefing-exec-insight-chip--fees">
          <div className="briefing-exec-insight-chip__head">
            <h3>Fee collection</h3>
          </div>
          <div className="fee-collection-panel">
            {pending > 0 ? (
              <div className="fee-collection-panel__decision">
                <p className="fee-collection-panel__headline">
                  <strong>{inrCompact(pending)}</strong> outstanding
                  {pendingFamilies > 0
                    ? ` across ${pendingFamilies} famil${pendingFamilies === 1 ? "y" : "ies"}`
                    : ""}
                </p>
                <p className="fee-collection-panel__subline">
                  {collectionRate}% collected · {inr(collected)} received to date
                </p>
                <Link href={FINANCE.fees} className="fee-collection-panel__cta">
                  Review collections
                </Link>
              </div>
            ) : (
              <p className="fee-collection-panel__subline fee-collection-panel__subline--solo">
                All fee accounts are settled — {inr(collected)} collected to date.
              </p>
            )}
            <FeeCollectionGauge
              rate={collectionRate}
              collected={collected}
              pending={pending}
            />
            <div className="fee-collection-panel__legend">
              <div className="fee-collection-panel__row">
                <span className="fee-collection-panel__key">
                  <span className="fee-collection-panel__dot fee-collection-panel__dot--collected" />
                  <span className="fee-collection-panel__label">Collected</span>
                </span>
                <strong className="fee-collection-panel__amount">{inr(collected)}</strong>
              </div>
              <div className="fee-collection-panel__row">
                <span className="fee-collection-panel__key">
                  <span className="fee-collection-panel__dot fee-collection-panel__dot--pending" />
                  <span className="fee-collection-panel__label">Outstanding</span>
                </span>
                <strong className="fee-collection-panel__amount">{inr(pending)}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
