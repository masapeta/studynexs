"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";

/** Printable per-student digest of approved/sent weakness notes —
 * the delivery vehicle for parent-teacher meetings until the parent portal ships. */
export default function MasteryDigestPage() {
  const router = useRouter();
  const [classes, setClasses] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [digest, setDigest] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => setClasses(r.items || r.data || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const url = classId ? `/api/v1/mastery/digest?class_id=${classId}` : "/api/v1/mastery/digest";
    api(url)
      .then((r) => setDigest(r.data))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load digest")));
  }, [classId]);

  return (
    <>
      <style>{`
        @media print {
          .no-print { display: none !important; }
          .digest-card { box-shadow: none !important; border: none !important; break-inside: avoid; }
        }
      `}</style>

      <div className="card no-print" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Parent Meeting Digest</h1>
        <div style={{ display: "flex", gap: 12 }}>
          <select className="form-input" style={{ width: 200, padding: "8px 12px" }} value={classId} onChange={(e) => setClassId(e.target.value)}>
            <option value="">All classes</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.grade} - {c.section}</option>
            ))}
          </select>
          <button className="btn btn-ghost" style={btn} onClick={() => router.push("/dashboard/mastery")}>← Back</button>
          <button className="btn btn-primary" style={btn} onClick={() => window.print()}>Print</button>
        </div>
      </div>

      {error && <div className="card no-print" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {digest && digest.students.length === 0 && (
        <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
          No approved notes yet. Approve flags in the review queue first.
        </div>
      )}

      <div style={{ marginBottom: 12, fontSize: 13, color: "var(--text-secondary)" }}>
        Generated {digest?.generated_on || ""} · Learning support notes, reviewed and approved by the class teacher.
      </div>

      {(digest?.students || []).map((entry: any) => (
        <div key={entry.student_id} className="card digest-card" style={{ padding: 20, marginBottom: 16 }}>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
            {entry.student_name}
            <span style={{ fontWeight: 400, fontSize: 13, color: "var(--text-muted)", marginLeft: 8 }}>
              {entry.flags[0]?.class_name}
            </span>
          </div>
          {entry.flags.map((f: any) => (
            <div key={f.id} style={{ padding: "10px 0", borderTop: "1px solid var(--border-light)" }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
                {(f.evidence || {}).subject_name} → {f.topic_display}
                <span style={{ fontWeight: 400, color: "var(--text-muted)" }}>
                  {" "}· mastery {(f.evidence || {}).mastery_pct}% (class avg {(f.evidence || {}).class_avg_pct}%)
                </span>
              </div>
              <div style={{ fontSize: 14, lineHeight: 1.6 }}>{f.narrative}</div>
            </div>
          ))}
        </div>
      ))}
    </>
  );
}

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
