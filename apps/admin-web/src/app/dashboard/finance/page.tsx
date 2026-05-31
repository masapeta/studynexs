"use client";

import { useEffect, useState } from "react";
import { api, API_URL } from "@/lib/api";

export default function FinancePage() {
  const [stats, setStats] = useState<any>({ total_collected: 0, pending_amount: 0, this_month: 0 });
  const [recent, setRecent] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, recentRes] = await Promise.all([
          api("/api/v1/fees/stats"),
          api("/api/v1/fees/recent?limit=10")
        ]);
        if (statsRes.data) setStats(statsRes.data);
        if (recentRes.data) setRecent(recentRes.data);
      } catch (err) {
        console.error("Finance fetch error", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Finance</h1>
      </div>

      {/* Fee Summary Cards */}
      <div className="bento-grid" style={{ marginBottom: 24 }}>
        <div className="card bento-col-4" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-green">
            ₹
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>Total Collected</div>
            {loading ? (
              <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
            ) : (
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>
                ₹ {stats.total_collected.toLocaleString()}
              </div>
            )}
          </div>
        </div>
        
        <div className="card bento-col-4" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-orange">
            ⚠
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>Pending Dues</div>
            {loading ? (
              <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
            ) : (
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>
                ₹ {stats.pending_amount.toLocaleString()}
              </div>
            )}
          </div>
        </div>
        
        <div className="card bento-col-4" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-blue">
            📅
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>This Month</div>
            {loading ? (
              <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
            ) : (
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>
                ₹ {stats.this_month.toLocaleString()}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Payments */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="data-table-header" style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-light)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>Recent Payments</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Receipt #</th>
              <th>Student</th>
              <th>Class</th>
              <th>Amount</th>
              <th>Mode</th>
              <th>Date</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: "center", padding: 40 }}>
                <div className="spinner" style={{ margin: "0 auto" }} />
              </td></tr>
            ) : recent.length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                No recent payments found
              </td></tr>
            ) : (
              recent.map((r) => (
                <tr key={r.id}>
                  <td style={{ fontWeight: 600 }}>{r.receipt_number}</td>
                  <td>{r.student_name}</td>
                  <td><span style={{ padding: "4px 8px", background: "var(--bg)", borderRadius: "var(--radius-sm)", fontSize: 12 }}>{r.class_name}</span></td>
                  <td style={{ fontWeight: 600, color: "var(--success)" }}>₹ {r.amount_paid.toLocaleString()}</td>
                  <td><span style={{ textTransform: "capitalize", fontSize: 12, color: "var(--text-secondary)" }}>{r.payment_mode}</span></td>
                  <td style={{ color: "var(--text-secondary)" }}>{new Date(r.paid_at).toLocaleDateString()}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button onClick={() => window.open(`${API_URL}/api/v1/fees/receipt/${r.receipt_number}`, '_blank')} className="btn" style={{ padding: "6px 14px", background: "var(--primary-50)", color: "var(--primary)", fontSize: 12, borderRadius: "var(--radius-full)" }}>
                      📄 View Receipt
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
