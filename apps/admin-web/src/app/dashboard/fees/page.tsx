"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { inr } from "@/lib/format";

type RosterRow = {
  student_id: string;
  name: string;
  class_label: string;
  total_due: number;
  paid_amount: number;
  status: string;
  fee_record_id: string | null;
};

const statusTone: Record<string, "green" | "brass" | "red" | "gray"> = {
  paid: "green",
  partial: "brass",
  overdue: "red",
  pending: "gray",
};

export default function FeesPage() {
  const [rows, setRows] = useState<RosterRow[]>([]);
  const [totalDue, setTotalDue] = useState(0);
  const [collected, setCollected] = useState(0);
  const [termLabel, setTermLabel] = useState("Term 1");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [paying, setPaying] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api<{
        data: { students: RosterRow[]; total_due: number; total_collected: number; term_label: string };
      }>("/api/v1/fees/roster");
      setRows(res.data?.students || []);
      setTotalDue(res.data?.total_due || 0);
      setCollected(res.data?.total_collected || 0);
      setTermLabel(res.data?.term_label || "Term 1");
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load fees"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function recordPayment(row: RosterRow) {
    if (!row.fee_record_id) return;
    const balance = row.total_due - row.paid_amount;
    if (balance <= 0) return;
    setPaying(row.student_id);
    try {
      await api("/api/v1/fees/pay", {
        method: "POST",
        body: JSON.stringify({
          fee_record_id: row.fee_record_id,
          amount: balance,
          payment_mode: "cash",
        }),
      });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Payment failed"));
    } finally {
      setPaying(null);
    }
  }

  const pct = totalDue > 0 ? Math.round((collected / totalDue) * 100) : 0;

  return (
    <PageShell
      title="Fees"
      subtitle={`${inr(collected)} collected of ${inr(totalDue)} · ${termLabel}`}
    >
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="gw-progress-bar" style={{ marginBottom: 20 }}>
        <div className="gw-progress-fill" style={{ width: `${pct}%` }} />
      </div>

      <div className="gw-card" style={{ overflow: "hidden" }}>
        <table className="data-table gw-table">
          <thead>
            <tr>
              <th>Student</th>
              <th>Class</th>
              <th>Paid</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="gw-center">
                  <div className="spinner" />
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="gw-muted gw-center">
                  No fee records found
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.student_id}>
                  <td style={{ fontWeight: 600 }}>{r.name}</td>
                  <td>{r.class_label}</td>
                  <td>
                    {inr(r.paid_amount)} / {inr(r.total_due)}
                  </td>
                  <td>
                    <StatusBadge tone={statusTone[r.status] || "gray"}>
                      {r.status.charAt(0).toUpperCase() + r.status.slice(1)}
                    </StatusBadge>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {r.status !== "paid" && r.fee_record_id && (
                      <button
                        type="button"
                        className="btn gw-btn-sage gw-btn-sm"
                        disabled={paying === r.student_id}
                        onClick={() => recordPayment(r)}
                      >
                        {paying === r.student_id ? "…" : "Record payment"}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </PageShell>
  );
}
