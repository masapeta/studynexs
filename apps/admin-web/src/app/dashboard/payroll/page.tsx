"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { inr } from "@/lib/format";

type PayrollRow = {
  entry_id: string;
  name: string;
  role: string;
  gross_amount: number;
  status: string;
};

export default function PayrollPage() {
  const [rows, setRows] = useState<PayrollRow[]>([]);
  const [totalGross, setTotalGross] = useState(0);
  const [paidGross, setPaidGross] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [marking, setMarking] = useState<string | null>(null);

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
    try {
      await api(`/api/v1/ops/payroll/${entryId}/mark-paid`, { method: "POST" });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not mark paid"));
    } finally {
      setMarking(null);
    }
  }

  return (
    <PageShell
      title="Payroll"
      subtitle={`${inr(paidGross)} disbursed of ${inr(totalGross)} monthly payroll`}
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
                  No payroll entries
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.entry_id}>
                  <td style={{ fontWeight: 600 }}>{r.name}</td>
                  <td style={{ textTransform: "capitalize" }}>{r.role}</td>
                  <td>{inr(r.gross_amount)}</td>
                  <td>
                    <StatusBadge tone={r.status === "paid" ? "green" : "brass"}>
                      {r.status === "paid" ? "Paid" : "Pending"}
                    </StatusBadge>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {r.status !== "paid" && (
                      <button
                        type="button"
                        className="btn gw-btn-sage gw-btn-sm"
                        disabled={marking === r.entry_id}
                        onClick={() => markPaid(r.entry_id)}
                      >
                        {marking === r.entry_id ? "…" : "Mark paid"}
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
