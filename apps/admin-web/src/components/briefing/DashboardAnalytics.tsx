"use client";

import { type CSSProperties } from "react";
import { inr } from "@/lib/format";

type ClassPerformance = { label: string; percentage: number };

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

  return (
    <section className="briefing-exec-insights" aria-labelledby="briefing-analytics-title">
      <div className="briefing-exec-section-head">
        <h2 id="briefing-analytics-title">Insights</h2>
        <p>Attendance and fee trends across the school</p>
      </div>

      <div className="briefing-exec-row briefing-exec-row--insights">
        <div className="briefing-glass-chip briefing-exec-insight-chip briefing-exec-insight-chip--attendance">
          <h3>Class attendance</h3>
          {classPerformance.length === 0 ? (
            <p className="gw-muted">No class performance data yet.</p>
          ) : (
            <div className="reports-bar-chart">
              {classPerformance.map((c) => (
                <div key={c.label} className="reports-bar-row">
                  <span className="reports-bar-label">{c.label}</span>
                  <div className="gw-progress-bar reports-bar-track">
                    <div
                      className="gw-progress-fill"
                      style={{ width: `${Math.min(100, c.percentage)}%` }}
                    />
                  </div>
                  <span className="reports-bar-value">{c.percentage}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="briefing-glass-chip briefing-exec-insight-chip briefing-exec-insight-chip--fees">
          <h3>Fee collection</h3>
          <div className="reports-fee-split">
            <div className="reports-fee-ring" style={{ "--pct": collectionRate } as CSSProperties}>
              <span>{collectionRate}%</span>
            </div>
            <div className="briefing-exec-fee-legend">
              <div className="reports-fee-line">
                <span>Collected</span>
                <strong>{inr(collected)}</strong>
              </div>
              <div className="reports-fee-line">
                <span>Outstanding</span>
                <strong>{inr(pending)}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
