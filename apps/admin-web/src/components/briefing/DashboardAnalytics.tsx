"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { Download, TrendingUp } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { inr } from "@/lib/format";

type Summary = {
  total_students?: number | null;
  total_teachers?: number | null;
  school_attendance_percent?: number | null;
  class_performance?: { label: string; percentage: number }[];
  admissions_pipeline?: number | null;
  expenses_this_month?: number | null;
};

type FeeStats = {
  total_collected?: number;
  pending_amount?: number;
};

/** School-wide analytics — embedded on the home dashboard (replaces standalone Reports page). */
export function DashboardAnalytics() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [fees, setFees] = useState<FeeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<{ data: Summary }>("/api/v1/dashboard/summary"),
      api<{ data: FeeStats }>("/api/v1/fees/stats").catch(() => ({ data: null })),
    ])
      .then(([s, f]) => {
        setSummary(s.data);
        setFees(f.data);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load analytics")))
      .finally(() => setLoading(false));
  }, []);

  const students = summary?.total_students ?? 0;
  const teachers = summary?.total_teachers ?? 0;
  const ratio = teachers > 0 ? (students / teachers).toFixed(1) : "—";
  const attendance = summary?.school_attendance_percent ?? 0;
  const collected = fees?.total_collected ?? 0;
  const pending = fees?.pending_amount ?? 0;
  const collectionRate =
    collected + pending > 0 ? Math.round((collected / (collected + pending)) * 100) : 0;
  const classBars = summary?.class_performance || [];

  return (
    <section className="briefing-analytics sn-section-gap" aria-labelledby="briefing-analytics-title">
      <div className="briefing-analytics-head">
        <div>
          <h2 id="briefing-analytics-title" className="briefing-analytics-title">
            School analytics
          </h2>
          <p className="briefing-analytics-sub">Operational insights at a glance</p>
        </div>
        <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => window.print()}>
          <Download size={14} /> Export
        </button>
      </div>

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}

      {loading ? (
        <div className="gw-center">
          <div className="spinner" />
        </div>
      ) : (
        <>
          <div className="reports-charts-grid">
            <div className="gw-card gw-card-pad">
              <h3 className="gw-list-title">Class attendance snapshot</h3>
              {classBars.length === 0 ? (
                <p className="gw-muted">No class performance data yet.</p>
              ) : (
                <div className="reports-bar-chart">
                  {classBars.map((c) => (
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

            <div className="gw-card gw-card-pad">
              <h3 className="gw-list-title">Fee collection</h3>
              <div className="reports-fee-split">
                <div className="reports-fee-ring" style={{ "--pct": collectionRate } as CSSProperties}>
                  <span>{collectionRate}%</span>
                </div>
                <div>
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

          <div className="gw-card gw-card-pad briefing-analytics-kpis">
            <div className="briefing-panel-head">
              <TrendingUp size={16} className="briefing-tone-sage" />
              <h3 className="gw-list-title">Key indicators</h3>
            </div>
            <div className="reports-kpi-grid">
              <div className="reports-kpi">
                <div className="gw-muted">Student–teacher ratio</div>
                <div className="reports-kpi-value">1:{ratio}</div>
              </div>
              <div className="reports-kpi">
                <div className="gw-muted">Today&apos;s attendance</div>
                <div className="reports-kpi-value">{attendance}%</div>
              </div>
              <div className="reports-kpi">
                <div className="gw-muted">Admissions pipeline</div>
                <div className="reports-kpi-value">{summary?.admissions_pipeline ?? 0}</div>
              </div>
              <div className="reports-kpi">
                <div className="gw-muted">Expenses this month</div>
                <div className="reports-kpi-value">{inr(summary?.expenses_this_month ?? 0)}</div>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
