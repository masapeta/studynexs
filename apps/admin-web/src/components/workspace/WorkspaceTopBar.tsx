"use client";

type SystemStatus = "live" | "degraded" | "off";

interface SystemPill {
  label: string;
  status: SystemStatus;
}

const SYSTEMS: SystemPill[] = [
  { label: "LMS", status: "live" },
  { label: "SIS", status: "live" },
  { label: "Exams", status: "live" },
  { label: "Attendance", status: "live" },
  { label: "Fees", status: "live" },
];

function dotClass(status: SystemStatus): string {
  if (status === "degraded") return "sn-ws-pill__dot sn-ws-pill__dot--warn";
  if (status === "off") return "sn-ws-pill__dot sn-ws-pill__dot--off";
  return "sn-ws-pill__dot";
}

export function WorkspaceTopBar({
  title,
  roleLabel,
  institution,
  right,
}: {
  title: string;
  roleLabel: string;
  institution: string;
  right?: React.ReactNode;
}) {
  return (
    <header className="sn-ws-topbar">
      <span className="sn-ws-topbar__title">{title}</span>
      <span className="sn-ws-badge">{roleLabel}</span>
      {institution ? <span className="sn-ws-topbar__ctx">{institution}</span> : null}

      <div className="sn-ws-topbar__spacer" />

      <div className="sn-ws-status" role="group" aria-label="System status">
        {SYSTEMS.map((s) => (
          <span key={s.label} className="sn-ws-pill" title={`${s.label}: ${s.status}`}>
            <span className={dotClass(s.status)} aria-hidden />
            {s.label}
          </span>
        ))}
      </div>

      {right}
    </header>
  );
}
