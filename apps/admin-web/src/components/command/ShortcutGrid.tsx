import React from "react";
import {
  FileText,
  CheckSquare,
  Clock,
  GraduationCap,
  TrendingUp,
  AlertCircle,
  FileSpreadsheet,
} from "lucide-react";

interface Shortcut {
  label: string;
  intent: string;
  icon: React.ElementType;
}

export const TEACHER_SHORTCUTS: Shortcut[] = [
  { label: "At-Risk Students", intent: "Show students below 75% attendance or declining marks", icon: AlertCircle },
  { label: "Leave Approvals", intent: "List student leave requests waiting for my approval", icon: CheckSquare },
  { label: "Assignment Queue", intent: "Show submissions pending grading and rubrics", icon: FileText },
  { label: "Weak Concepts", intent: "Which topics in Chapter 4 had the highest error rate?", icon: TrendingUp },
  { label: "Exam Eligibility", intent: "Show students with attendance condonation flags", icon: GraduationCap },
];

export const ADMIN_SHORTCUTS: Shortcut[] = [
  { label: "Hall Ticket Readiness", intent: "Show institution-wide exam fee and attendance clearance", icon: FileSpreadsheet },
  { label: "Certificate Approvals", intent: "Show pending bonafide and transfer certificate requests", icon: CheckSquare },
  { label: "Fee Hold Exceptions", intent: "List students with fee-hold registration blocks", icon: AlertCircle },
  { label: "Staff Overview", intent: "Show staff on leave and substitution gaps today", icon: Clock },
];

export function ShortcutGrid({
  shortcuts,
  onShortcutClick,
}: {
  shortcuts: Shortcut[];
  onShortcutClick: (intent: string) => void;
}) {
  return (
    <div
      style={{
        display: "grid",
        gap: 12,
        gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
      }}
    >
      {shortcuts.map((s) => {
        const Icon = s.icon;
        return (
          <button
            key={s.label}
            type="button"
            onClick={() => onShortcutClick(s.intent)}
            className="card ui-card-tap"
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              gap: 12,
              padding: 16,
              margin: 0,
              textAlign: "left",
              cursor: "pointer",
            }}
          >
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: 40,
                height: 40,
                borderRadius: 12,
                background: "var(--accent-50)",
                color: "var(--accent-dark)",
              }}
            >
              <Icon size={20} strokeWidth={1.9} />
            </span>
            <span
              style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3 }}
            >
              {s.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
