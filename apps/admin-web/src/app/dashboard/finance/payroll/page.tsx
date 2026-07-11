"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { inr } from "@/lib/format";

type PayrollRow = {
  user_id: string;
  // null when this month's payroll hasn't been generated for the staff member yet.
  entry_id: string | null;
  name: string;
  role: string;
  gross_amount: number;
  status: string;
};

function statusLabel(status: string): { tone: "green" | "brass"; label: string } {
  if (status === "paid") return { tone: "green", label: "Paid" };
  if (status === "not_generated") return { tone: "brass", label: "Not set up" };
  return { tone: "brass", label: "Pending" };
}

export default function PayrollPage() {
  const [rows, setRows] = useState<PayrollRow[]>([]);
  const [totalGross, setTotalGross] = useState(0);
  const [paidGross, setPaidGross] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [marking, setMarking] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api<{
        data: { entries: PayrollRow[]; total_gross: number; paid_gross: number };
      }>("/api/v1/ops/payroll");
      setRows(res.data?.entries || []);
      setTotalGross(res.data?.total_gross || 0);
      setPaidGross(res.data?.paid_gross || 0);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load payroll"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function markPaid(entryId: string) {
    setMarking(entryId);
    setError("");
    try {
      await api(`/api/v1/ops/payroll/${entryId}/mark-paid`, { method: "POST" });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not mark paid"));
    } finally {
      setMarking(null);
    }
  }

  async function generatePayroll() {
    setGenerating(true);
    setError("");
    try {
      await api("/api/v1/ops/payroll/generate", { method: "POST" });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not generate payroll"));
    } finally {
      setGenerating(false);
    }
  }

  const ungenerated = rows.filter((r) => r.entry_id === null).length;

  return (
    <PageShell
      title="Payroll"
      subtitle={`${inr(paidGross)} disbursed of ${inr(totalGross)} monthly payroll`}
      action={
        ungenerated > 0 ? (
          <button
            type="button"
            className="btn gw-btn-sage gw-btn-sm"
            disabled={generating}
            onClick={generatePayroll}
          >
            {generating ? "Generating…" : `Generate payroll (${ungenerated})`}
          </button>
        ) : undefined
      }
    >
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="gw-card" style={{ overflow: "hidden" }}>
        <table className="data-table gw-table">
          <thead>
            <tr>
              <th>Staff</th>
              <th>Role</th>
              <th>Gross / month</th>
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
                  No staff to pay yet
                </td>
              </tr>
            ) : (
              rows.map((r) => {
                const badge = statusLabel(r.status);
                return (
                  <tr key={r.user_id}>
                    <td style={{ fontWeight: 600 }}>{r.name}</td>
                    <td style={{ textTransform: "capitalize" }}>{r.role}</td>
                    <td>{inr(r.gross_amount)}</td>
                    <td>
                      <StatusBadge tone={badge.tone}>{badge.label}</StatusBadge>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {r.entry_id && r.status !== "paid" && (
                        <button
                          type="button"
                          className="btn gw-btn-sage gw-btn-sm"
                          disabled={marking === r.entry_id}
                          onClick={() => markPaid(r.entry_id!)}
                        >
                          {marking === r.entry_id ? "…" : "Mark paid"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </PageShell>
  );
}
