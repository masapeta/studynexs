"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ClassesPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetch() {
      try {
        const res = await api("/api/v1/academic/classes");
        setClasses(res.items || res.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetch();
  }, []);

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Classes</h1>
        <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }}>+ Add Class</button>
      </div>

      <div className="dashboard-grid">
        {loading ? (
          <div className="card" style={{ gridColumn: "1/-1", textAlign: "center", padding: 40 }}>
            <div className="spinner" style={{ margin: "0 auto" }} />
          </div>
        ) : classes.length === 0 ? (
          <div className="card" style={{ gridColumn: "1/-1", textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
            No classes found. Create your first class.
          </div>
        ) : (
          classes.map((c: any) => (
            <div key={c.id} className="card" style={{ cursor: "pointer" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: "var(--radius-md)",
                  background: "linear-gradient(135deg, var(--primary), #8b5cf6)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "white", fontWeight: 700, fontSize: 16
                }}>
                  {c.grade?.charAt(0) || "C"}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{c.grade} - {c.section}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {c.student_count || 0} students
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <div style={{ flex: 1, background: "var(--success-light)", borderRadius: "var(--radius-sm)", padding: "8px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Attendance</div>
                  <div style={{ fontWeight: 700, color: "var(--success)" }}>94%</div>
                </div>
                <div style={{ flex: 1, background: "var(--primary-50)", borderRadius: "var(--radius-sm)", padding: "8px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Avg Score</div>
                  <div style={{ fontWeight: 700, color: "var(--primary)" }}>78%</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}
