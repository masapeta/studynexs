"use client";

import { useEffect, useState } from "react";
import { Users, CalendarDays } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function NoticesPage() {
  const { permissions } = useAuth();
  const canPublish =
    permissions?.can_publish_notices ||
    permissions?.can_publish_class_notices ||
    permissions?.can_publish_internal_notices;
  const [notices, setNotices] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    content: "",
    audience: "external" as "internal" | "external",
    target_roles: ["student", "parent"] as string[],
    priority: "medium",
    class_id: "",
  });

  async function loadNotices() {
    const res = await api("/api/v1/notices");
    setNotices(res.data || []);
  }

  useEffect(() => {
    async function fetch() {
      try {
        await loadNotices();
        if (permissions?.can_publish_class_notices) {
          const cls = await api("/api/v1/academic/classes?page_size=100");
          const items = cls.items || cls.data || [];
          setClasses(items);
          if (items[0] && !permissions?.can_publish_notices) {
            setForm((f) => ({ ...f, class_id: items[0].id }));
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (permissions) fetch();
  }, [permissions]);

  async function publish() {
    if (!form.title.trim() || !form.content.trim()) {
      setError("Title and content are required.");
      return;
    }
    if (form.audience === "external" && permissions?.can_publish_class_notices && !permissions?.can_publish_notices && !form.class_id) {
      setError("Select a class for parent/student notices.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/notices", {
        method: "POST",
        body: JSON.stringify({
          title: form.title,
          content: form.content,
          audience: form.audience,
          target_roles: form.target_roles,
          priority: form.priority,
          class_id: form.class_id || null,
        }),
      });
      setForm({
        title: "", content: "", audience: "external",
        target_roles: ["student", "parent"], priority: "medium", class_id: form.class_id,
      });
      setShowForm(false);
      await loadNotices();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to publish notice."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Notices & Announcements</h1>
        {canPublish && (
          <button
            className="btn btn-primary"
            style={{ width: "auto", padding: "10px 20px" }}
            onClick={() => setShowForm((v) => !v)}
          >
            {showForm ? "Cancel" : "+ New Notice"}
          </button>
        )}
      </div>

      {showForm && canPublish && (
        <div className="card" style={{ padding: 20, marginBottom: 20 }}>
          {error && <div style={{ color: "var(--danger)", marginBottom: 12 }}>{error}</div>}
          {permissions?.can_publish_internal_notices && (
            <div style={{ marginBottom: 12 }}>
              <label className="stat-label">Notice type</label>
              <select
                className="form-input"
                value={form.audience}
                onChange={(e) => {
                  const audience = e.target.value as "internal" | "external";
                  setForm({
                    ...form,
                    audience,
                    target_roles: audience === "internal"
                      ? ["teacher", "class_incharge"]
                      : ["student", "parent"],
                  });
                }}
                style={{ width: "100%", marginTop: 4 }}
              >
                <option value="external">Parents / Students</option>
                <option value="internal">Staff only (internal circular)</option>
              </select>
            </div>
          )}
          {form.audience === "external" && permissions?.can_publish_class_notices && (
            <div style={{ marginBottom: 12 }}>
              <label className="stat-label">Class {permissions?.can_publish_notices ? "(optional)" : ""}</label>
              <select
                className="form-input"
                value={form.class_id}
                onChange={(e) => setForm({ ...form, class_id: e.target.value })}
                style={{ width: "100%", marginTop: 4 }}
              >
                {permissions?.can_publish_notices && <option value="">School-wide</option>}
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.grade} - {c.section}</option>
                ))}
              </select>
            </div>
          )}
          <input
            className="form-input"
            placeholder="Notice title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            style={{ width: "100%", marginBottom: 12 }}
          />
          <textarea
            className="form-input"
            placeholder="Message to students and parents…"
            value={form.content}
            onChange={(e) => setForm({ ...form, content: e.target.value })}
            rows={4}
            style={{ width: "100%", marginBottom: 12 }}
          />
          <button className="btn btn-primary" onClick={publish} disabled={saving} style={{ width: "auto", padding: "10px 24px" }}>
            {saving ? "Publishing…" : "Publish"}
          </button>
        </div>
      )}

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
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  <Users size={13} />
                  {n.audience === "internal" ? "Staff" : (n.target_roles || []).join(", ")}
                </span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><CalendarDays size={13} /> {n.created_at ? new Date(n.created_at).toLocaleDateString() : "—"}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
