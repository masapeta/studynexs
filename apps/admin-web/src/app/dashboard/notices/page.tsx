"use client";

import { useEffect, useState } from "react";
import { Megaphone } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { PageShell } from "@/components/layout/PageShell";
import { AppSelect } from "@/components/ui/AppSelect";
import { StatusBadge } from "@/components/briefing/StatusBadge";

type AudienceKey = "all" | "parents" | "students" | "staff";

const AUDIENCE_MAP: Record<
  AudienceKey,
  { label: string; audience: "internal" | "external"; target_roles: string[] }
> = {
  all: { label: "All", audience: "external", target_roles: ["student", "parent", "teacher", "class_incharge"] },
  parents: { label: "Parents", audience: "external", target_roles: ["parent"] },
  students: { label: "Students", audience: "external", target_roles: ["student"] },
  staff: { label: "Staff", audience: "internal", target_roles: ["teacher", "class_incharge", "admin", "operations"] },
};

function audienceLabel(n: { audience?: string; target_roles?: string[] }) {
  if (n.audience === "internal") return "Staff";
  const roles = n.target_roles || [];
  if (roles.includes("parent") && roles.includes("student")) return "Parents & Students";
  if (roles.includes("parent")) return "Parents";
  if (roles.includes("student")) return "Students";
  if (n.audience === "external") return "Parents & Students";
  return "School-wide";
}

function timeAgo(iso?: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  const days = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

export default function NoticesPage() {
  const { user, permissions } = useAuth();
  const canPublish =
    permissions?.can_publish_notices ||
    permissions?.can_publish_class_notices ||
    permissions?.can_publish_internal_notices;
  const [notices, setNotices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    content: "",
    audienceKey: "all" as AudienceKey,
  });

  async function loadNotices() {
    const res = await api("/api/v1/notices");
    setNotices(res.data || []);
  }

  useEffect(() => {
    if (!permissions) return;
    loadNotices().finally(() => setLoading(false));
  }, [permissions]);

  async function publish() {
    if (!form.title.trim() || !form.content.trim()) {
      setError("Headline and details are required.");
      return;
    }
    const map = AUDIENCE_MAP[form.audienceKey];
    if (map.audience === "internal" && !permissions?.can_publish_internal_notices) {
      setError("You cannot post staff-only notices.");
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
          audience: map.audience,
          target_roles: map.target_roles,
          priority: "medium",
          class_id: null,
        }),
      });
      setForm({ title: "", content: "", audienceKey: "all" });
      await loadNotices();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to post notice."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageShell
      title="Notices & Communication"
      subtitle="Post announcements to parents, students and staff."
    >
      {canPublish && (
        <div className="gw-card gw-card-pad gw-notice-compose">
          {error && <div className="gw-alert gw-alert-error">{error}</div>}
          <input
            className="form-input"
            placeholder="Notice headline"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <textarea
            className="form-input"
            placeholder="Write the details…"
            value={form.content}
            onChange={(e) => setForm({ ...form, content: e.target.value })}
            rows={3}
          />
          <div className="gw-notice-compose-row">
            <AppSelect
              variant="field"
              value={form.audienceKey}
              onChange={(v) => setForm({ ...form, audienceKey: v as AudienceKey })}
              aria-label="Notice audience"
              style={{ maxWidth: 160 }}
              options={(Object.keys(AUDIENCE_MAP) as AudienceKey[]).map((k) => ({
                value: k,
                label: AUDIENCE_MAP[k].label,
              }))}
            />
            <button
              type="button"
              className="btn gw-btn-brass"
              onClick={publish}
              disabled={saving}
              style={{ width: "auto", padding: "10px 20px" }}
            >
              <Megaphone size={16} /> {saving ? "Posting…" : "Post notice"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="gw-center"><div className="spinner" /></div>
      ) : notices.length === 0 ? (
        <p className="gw-muted">No notices published yet.</p>
      ) : (
        <div className="gw-notice-feed">
          {notices.map((n: any) => (
            <article key={n.id} className="gw-card gw-notice-card">
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>
                <h3>{n.title}</h3>
                <StatusBadge tone="brass">{audienceLabel(n)}</StatusBadge>
              </div>
              <p>{n.content}</p>
              <div className="gw-notice-footer">
                {user?.full_name?.split(" ")[0] ? `${n.author_name || user.full_name}` : "Staff"} · {timeAgo(n.created_at)}
              </div>
            </article>
          ))}
        </div>
      )}
    </PageShell>
  );
}
