"use client";

import { inr } from "@/lib/format";
import { ClassAttendanceChart, formatAttendanceChartDate, type ClassAttendanceBar } from "./ClassAttendanceChart";
import { FeeCollectionGauge } from "./FeeCollectionGauge";

type ClassPerformance = ClassAttendanceBar;

type FeeStats = {
  total_collected?: number;
  pending_amount?: number;
};

type Props = {
  classPerformance?: ClassPerformance[];
  feeStats?: FeeStats | null;
};

/** School-wide analytics — uses dashboard data when provided (no extra fetch). */
export function DashboardAnalytics({ classPerformance = [], feeStats }: Props) {
  const collected = feeStats?.total_collected ?? 0;
  const pending = feeStats?.pending_amount ?? 0;
  const collectionRate =
    collected + pending > 0 ? Math.round((collected / (collected + pending)) * 100) : 0;
  const attendanceDateLabel = formatAttendanceChartDate(classPerformance[0]?.date);

  return (
    <section className="briefing-exec-insights" aria-labelledby="briefing-analytics-title">
      <div className="briefing-exec-section-head">
        <h2 id="briefing-analytics-title">Insights</h2>
        <p>Attendance and fee trends across the school</p>
      </div>

      <div className="briefing-exec-row briefing-exec-row--insights">
        <div className="briefing-glass-chip briefing-exec-insight-chip briefing-exec-insight-chip--attendance">
          <div className="briefing-exec-insight-chip__head">
            <h3>Class attendance</h3>
            {attendanceDateLabel ? (
              <span className="briefing-exec-insight-chip__meta">{attendanceDateLabel}</span>
            ) : null}
          </div>
          <ClassAttendanceChart data={classPerformance} />
        </div>

        <div className="briefing-glass-chip briefing-exec-insight-chip briefing-exec-insight-chip--fees">
          <div className="briefing-exec-insight-chip__head">
            <h3>Fee collection</h3>
          </div>
          <div className="fee-collection-panel">
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
