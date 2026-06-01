"use client";

import { useEffect, useState } from "react";
import { Users, CalendarDays } from "lucide-react";
import { api } from "@/lib/api";

export default function NoticesPage() {
  const [notices, setNotices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetch() {
      try {
        const res = await api("/api/v1/notices");
        setNotices(res.data || []);
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
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Notices & Announcements</h1>
        <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }}>+ New Notice</button>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 40 }}><div className="spinner" style={{ margin: "0 auto" }} /></div>
      ) : notices.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
          No notices published yet.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {notices.map((n: any) => (
            <div key={n.id} className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{n.title}</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>{n.content}</div>
                </div>
                <span style={{
                  padding: "4px 10px", borderRadius: "var(--radius-full)", fontSize: 11, fontWeight: 600,
                  background: n.priority === "high" ? "var(--danger-light)" : n.priority === "medium" ? "var(--warning-light)" : "var(--success-light)",
                  color: n.priority === "high" ? "var(--danger)" : n.priority === "medium" ? "var(--warning)" : "var(--success)",
                }}>
                  {n.priority}
                </span>
              </div>
              <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><Users size={13} /> {(n.target_roles || []).join(", ")}</span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><CalendarDays size={13} /> {n.created_at ? new Date(n.created_at).toLocaleDateString() : "—"}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
