"use client";

import { useEffect, useState } from "react";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";
import { STUDENT_NAV } from "@/lib/student-portal";
import type { MasteryData, MasterySubject, PortalContext } from "@/lib/portal-types";

const NAV = STUDENT_NAV;

export default function StudentMasteryPage() {
  const [mastery, setMastery] = useState<MasteryData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api<{ data: PortalContext }>("/api/v1/portal/context")
      .then(async (r) => {
        const sid = r.data?.children?.[0]?.student_id ?? r.data?.student_id;
        if (!sid) return null;
        return api<{ data: MasteryData }>(`/api/v1/mastery/students/${sid}`);
      })
      .then((m) => {
        if (active && m) setMastery(m.data);
      })
      .catch((e) => {
        if (active) setError(getApiErrorMessage(e, "Failed to load"));
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <PortalShell title="Mastery" subtitle="Topic-wise progress" nav={NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!mastery ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : (mastery.subjects || []).length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>Mastery builds after teachers enter exam marks.</p>
      ) : (
        (mastery.subjects || []).map((subject: MasterySubject) => (
          <div key={subject.subject_name} className="portal-card">
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{subject.subject_name}</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
              {(subject.topics || []).slice(0, 6).map((topic) => (
                <li key={topic.topic}>
                  {topic.topic}: {Math.round(topic.mastery_pct)}%
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </PortalShell>
  );
}
