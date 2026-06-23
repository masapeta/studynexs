"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { homePathForRole } from "@/lib/portal";

type Feature = {
  id: string;
  title: string;
  description: string;
  status: string;
  href?: string;
};

const STATUS_LABEL: Record<string, string> = {
  live: "Live",
  preview: "Preview",
  coming_soon: "Coming soon",
};

export default function DemoRoadmapPage() {
  const { user } = useAuth();
  const [features, setFeatures] = useState<Feature[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ data: Feature[] }>("/api/v1/portal/features")
      .then((r) => setFeatures(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load roadmap")));
  }, []);

  const home = user ? homePathForRole(user.role) : "/";

  return (
    <PortalShell title="Product roadmap" subtitle="What ships in pilot vs next" nav={[{ href: home, label: "Back" }]}>
      <Link href={home} style={{ fontSize: 13, marginBottom: 12, display: "inline-block" }}>← Back</Link>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {features.length === 0 && !error ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : (
        features.map((f) => (
          <div key={f.id} className="portal-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
              <div style={{ fontWeight: 700 }}>{f.title}</div>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: "4px 8px",
                  borderRadius: 6,
                  background:
                    f.status === "live"
                      ? "var(--success-light)"
                      : f.status === "preview"
                        ? "var(--info-light)"
                        : "var(--warning-light)",
                  color:
                    f.status === "live"
                      ? "var(--success)"
                      : f.status === "preview"
                        ? "var(--info)"
                        : "var(--warning)",
                  whiteSpace: "nowrap",
                }}
              >
                {STATUS_LABEL[f.status] || f.status}
              </span>
            </div>
            <p style={{ fontSize: 14, color: "var(--text-muted)", margin: "8px 0 0" }}>{f.description}</p>
            {f.href && f.status === "live" && (
              <Link href={f.href} style={{ fontSize: 13, fontWeight: 600, marginTop: 10, display: "inline-block" }}>
                Open →
              </Link>
            )}
          </div>
        ))
      )}
      <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 16 }}>
        Install this site as an app: Add to Home Screen on your phone (PWA).
      </p>
    </PortalShell>
  );
}
