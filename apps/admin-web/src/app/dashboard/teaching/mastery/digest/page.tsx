"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { TEACHING } from "@/lib/dashboard-routes";

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
      .then((r) => setClasses(sortClasses<any>(r.items || r.data || [])))
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

      <PageHeaderCard title="Parent Meeting Digest">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <AppSelect
            variant="pill"
            value={classId}
            onChange={setClassId}
            aria-label="Filter by class"
            className="sn-search-inline"
            placeholder="All classes"
            options={[
              { value: "", label: "All classes" },
              ...classes.map((c) => ({
                value: c.id,
                label: formatClassLabel(c.grade, c.section),
              })),
            ]}
          />
          <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => router.push(TEACHING.mastery)}>← Back</button>
          <button type="button" className="btn btn-primary gw-btn-sm" onClick={() => window.print()}>Print</button>
        </div>
      </PageHeaderCard>

      {error && <div className="card no-print sn-inline-alert sn-inline-alert--error">{error}</div>}

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
