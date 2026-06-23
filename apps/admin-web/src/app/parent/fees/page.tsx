"use client";

import { useEffect, useState } from "react";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";

const NAV = [
  { href: "/parent", label: "Home" },
  { href: "/parent/notices", label: "Notices" },
  { href: "/parent/fees", label: "Fees" },
  { href: "/demo/roadmap", label: "More" },
];

export default function ParentFeesPage() {
  const [ctx, setCtx] = useState<any>(null);
  const [feesByChild, setFeesByChild] = useState<Record<string, any[]>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/portal/context")
      .then(async (r) => {
        setCtx(r.data);
        const map: Record<string, any[]> = {};
        for (const c of r.data.children || []) {
          try {
            const res = await api(`/api/v1/fees/student/${c.student_id}`);
            map[c.student_id] = res.data || [];
          } catch {
            map[c.student_id] = [];
          }
        }
        setFeesByChild(map);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load")));
  }, []);

  return (
    <PortalShell title="Fees" subtitle="Due & paid" nav={NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!ctx ? <div className="spinner" style={{ margin: "40px auto" }} /> : (
        (ctx.children || []).map((c: any) => (
          <div key={c.student_id} className="portal-card">
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{c.name}</div>
            {(feesByChild[c.student_id] || []).length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>₹{c.fee_pending} pending · Pay online coming in pilot Phase 2</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {(feesByChild[c.student_id] || []).map((f: any) => (
                  <li key={f.id}>{f.fee_type || "Fee"}: ₹{f.amount} — {f.status}</li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
    </PortalShell>
  );
}
