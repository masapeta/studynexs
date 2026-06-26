"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ClipboardCheck,
  FileText,
  Home,
  Sparkles,
  Target,
} from "lucide-react";
import PortalShell from "@/components/PortalShell";
import type { NavItem } from "@/components/PortalShell";
import { TeacherCommandCenter, type TeacherHome } from "@/components/TeacherCommandCenter";
import { api, getApiErrorMessage } from "@/lib/api";

const NAV: NavItem[] = [
  { href: "/teacher", label: "Home", icon: Home },
  { href: "/dashboard/ai-papers", label: "AI Papers", icon: Sparkles },
  { href: "/dashboard/exams", label: "Exams", icon: FileText },
  { href: "/dashboard/mastery", label: "Mastery", icon: Target },
  { href: "/dashboard/attendance", label: "Attendance", icon: ClipboardCheck },
];

export default function TeacherHomePage() {
  const [teacherHome, setTeacherHome] = useState<TeacherHome | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => {
    setLoading(true);
    setError("");
    setRefreshKey((key) => key + 1);
  }, []);

  useEffect(() => {
    let active = true;
    api<{ data: { teacher_home?: TeacherHome | null } }>("/api/v1/dashboard/summary")
      .then((r) => {
        if (active) setTeacherHome(r.data?.teacher_home ?? null);
      })
      .catch((e) => {
        if (active) setError(getApiErrorMessage(e, "Could not load your workspace"));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshKey]);

  return (
    <PortalShell title="Teacher" subtitle="Your classes and tasks for today" nav={NAV}>
      {loading ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : error ? (
        <div className="portal-card">
          <p style={{ color: "var(--danger)", marginBottom: 12 }}>{error}</p>
          <button type="button" className="btn btn-primary" onClick={refresh}>
            Retry
          </button>
        </div>
      ) : teacherHome ? (
        <TeacherCommandCenter data={teacherHome} onRefresh={refresh} />
      ) : (
        <div className="portal-card">
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
            No teaching assignments are linked to your account yet.
          </p>
        </div>
      )}
    </PortalShell>
  );
}
