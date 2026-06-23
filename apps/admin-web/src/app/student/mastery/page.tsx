"use client";

import { useEffect, useState } from "react";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";
import { STUDENT_NAV } from "@/lib/student-portal";

const NAV = STUDENT_NAV;

export default function StudentMasteryPage() {
  const [ctx, setCtx] = useState<any>(null);
  const [mastery, setMastery] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/portal/context")
      .then(async (r) => {
        setCtx(r.data);
        const sid = r.data?.children?.[0]?.student_id ?? r.data?.student_id;
        if (sid) {
          const m = await api(`/api/v1/mastery/students/${sid}`);
          setMastery(m.data);
        }
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load")));
  }, []);

  return (
    <PortalShell title="Mastery" subtitle="Topic-wise progress" nav={NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!mastery ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : (mastery.subjects || []).length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>Mastery builds after teachers enter exam marks.</p>
      ) : (
        (mastery.subjects || []).map((s: any) => (
          <div key={s.subject_id || s.subject_name} className="portal-card">
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{s.subject_name}</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
              {(s.topics || []).slice(0, 6).map((t: any) => (
                <li key={t.topic}>{t.topic}: {Math.round(t.mastery_pct)}%</li>
              ))}
            </ul>
          </div>
        ))
      )}
    </PortalShell>
  );
}
