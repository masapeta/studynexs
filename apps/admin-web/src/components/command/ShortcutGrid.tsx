import React from 'react';
import { Sparkles, FileText, CheckSquare, Clock, GraduationCap, TrendingUp, AlertCircle, FileSpreadsheet } from 'lucide-react';

interface Shortcut {
  label: string;
  intent: string;
  icon: React.ElementType;
}

export const TEACHER_SHORTCUTS: Shortcut[] = [
  { label: 'At-Risk Students', intent: 'Show students below 75% attendance or declining marks', icon: AlertCircle },
  { label: 'Leave Approvals', intent: 'List student leave requests waiting for my approval', icon: CheckSquare },
  { label: 'Assignment Queue', intent: 'Show submissions pending grading and rubrics', icon: FileText },
  { label: 'Weak Concepts', intent: 'Which topics in Chapter 4 had the highest error rate?', icon: TrendingUp },
  { label: 'Exam Eligibility', intent: 'Show students with attendance condonation flags', icon: GraduationCap },
];

export const ADMIN_SHORTCUTS: Shortcut[] = [
  { label: 'Hall Ticket Readiness', intent: 'Show institution-wide exam fee and attendance clearance', icon: FileSpreadsheet },
  { label: 'Certificate Approvals', intent: 'Show pending bonafide and transfer certificate requests', icon: CheckSquare },
  { label: 'Fee Hold Exceptions', intent: 'List students with fee-hold registration blocks', icon: AlertCircle },
  { label: 'Staff Overview', intent: 'Show staff on leave and substitution gaps today', icon: Clock },
];

export function ShortcutGrid({ shortcuts, onShortcutClick }: { shortcuts: Shortcut[], onShortcutClick: (intent: string) => void }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full">
      {shortcuts.map((s) => (
        <button
          key={s.label}
          type="button"
          onClick={() => onShortcutClick(s.intent)}
          className="flex flex-col items-center justify-center gap-3 p-4 rounded-xl border border-line/60 bg-surface/40 hover:bg-surface hover:border-accent/40 shadow-[0_2px_10px_rgba(0,0,0,0.03)] transition-all text-center group cursor-pointer"
        >
          <div className="p-3 rounded-full bg-mist/50 text-muted group-hover:text-accent group-hover:bg-accent/10 transition-colors shadow-2xs">
            <s.icon size={22} strokeWidth={1.8} />
          </div>
          <span className="text-[13px] font-semibold text-ink leading-tight">{s.label}</span>
        </button>
      ))}
    </div>
  );
}
