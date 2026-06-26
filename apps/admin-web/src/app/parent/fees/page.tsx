"use client";

import { useEffect, useState } from "react";
import PortalShell from "@/components/PortalShell";
import { PARENT_NAV } from "@/lib/portal-nav";
import { api, getApiErrorMessage } from "@/lib/api";
import type { ParentChildFees } from "@/lib/portal-types";

export default function ParentFeesPage() {
  const [children, setChildren] = useState<ParentChildFees[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ data: ParentChildFees[] }>("/api/v1/portal/parent/fees")
      .then((r) => setChildren(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PortalShell title="Fees" subtitle="Due & paid" nav={PARENT_NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {loading ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : children.length === 0 ? (
        <div className="portal-card">
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No fee records linked to your account yet.</p>
        </div>
      ) : (
        children.map((child) => (
          <div key={child.student_id} className="portal-card">
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{child.name}</div>
            {child.records.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No fee line items yet.</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {child.records.map((fee) => (
                  <li key={fee.id}>
                    {fee.fee_type || "Fee"}: ₹{fee.amount} — {fee.status}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
    </PortalShell>
  );
}
