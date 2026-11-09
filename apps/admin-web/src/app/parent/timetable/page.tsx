"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { EmptyState, SkeletonCard } from "@/components/ui/kit";
import { LearnerTimetable } from "@/components/results/LearnerTimetable";
import { api, getApiErrorMessage } from "@/lib/api";
import { PARENT_NAV } from "@/lib/portal-nav";

type Child = { student_id: string; name: string; class_label: string };

export default function ParentTimetablePage() {
  const [children, setChildren] = useState<Child[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api<{ data: Child[] }>("/api/v1/portal/parent/children-progress")
      .then((r) => alive && setChildren(r.data ?? []))
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load your children.")));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <PortalShell title="Timetable" subtitle="Your children's class schedules" nav={PARENT_NAV}>
      {error ? (
        <p role="alert" style={{ color: "var(--danger)" }}>{error}</p>
      ) : children === null ? (
        <SkeletonCard />
      ) : children.length === 0 ? (
        <EmptyState icon={Users} title="No children linked yet" message="Timetables appear once the school links your children." />
      ) : (
        children.map((c) => (
          <LearnerTimetable key={c.student_id} title={`${c.name} · ${c.class_label}`} endpoint={`/api/v1/portal/child/${c.student_id}/timetable`} />
        ))
      )}
    </PortalShell>
  );
}
