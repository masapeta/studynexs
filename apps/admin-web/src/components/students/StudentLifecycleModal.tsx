"use client";

import { useMemo, useState } from "react";
import { X } from "lucide-react";
import { ModalBackdrop } from "@/components/layout/ModalBackdrop";
import { AppSelect } from "@/components/ui/AppSelect";
import { api, getApiErrorMessage } from "@/lib/api";

export type LifecycleAction =
  | "change-class"
  | "transfer-out"
  | "withdraw"
  | "mark-alumni"
  | "readmit";

export type LifecycleClassOption = {
  id: string;
  grade: string;
  section: string;
};

type LifecycleResult = {
  student_status: string;
  class_id: string;
  fee_review_required: boolean;
  fee_review_note: string | null;
};

const COPY: Record<
  LifecycleAction,
  { title: string; subtitle: string; submit: string; destructive: boolean; needsClass: boolean }
> = {
  "change-class": {
    title: "Change class",
    subtitle:
      "Move this student to another class in the same academic year. Past attendance, marks, and receipts stay with the class they were recorded against.",
    submit: "Change class",
    destructive: false,
    needsClass: true,
  },
  "transfer-out": {
    title: "Transfer out",
    subtitle: "Record that this student is leaving for another school.",
    submit: "Transfer out",
    destructive: true,
    needsClass: false,
  },
  withdraw: {
    title: "Withdraw student",
    subtitle: "Remove this student from the active roll.",
    submit: "Withdraw",
    destructive: true,
    needsClass: false,
  },
  "mark-alumni": {
    title: "Mark as alumni",
    subtitle: "Record that this student has completed their final grade.",
    submit: "Mark as alumni",
    destructive: false,
    needsClass: false,
  },
  readmit: {
    title: "Re-admit student",
    subtitle: "Bring this student back onto the active roll.",
    submit: "Re-admit",
    destructive: false,
    needsClass: true,
  },
};

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="gw-form-field">
      <span className="gw-form-label">
        {label}
        {required && <span className="gw-form-required">*</span>}
      </span>
      {children}
    </label>
  );
}

type Props = {
  open: boolean;
  action: LifecycleAction | null;
  studentId: string;
  studentName: string;
  currentClassId?: string;
  classes: LifecycleClassOption[];
  onClose: () => void;
  onDone: (result: LifecycleResult) => void;
};

function LifecycleForm({
  action,
  studentId,
  studentName,
  currentClassId,
  classes,
  onClose,
  onDone,
}: Omit<Props, "open"> & { action: LifecycleAction }) {
  const [classId, setClassId] = useState("");
  const [reason, setReason] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const copy = COPY[action];

  const classOptions = useMemo(
    () => [
      { value: "", label: "Select class…" },
      ...classes
        .filter((c) => c.id !== currentClassId)
        .map((c) => ({ value: c.id, label: `${c.grade}-${c.section}` })),
    ],
    [classes, currentClassId]
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (copy.needsClass && !classId) {
      setError("Select a class to continue.");
      return;
    }
    if (reason.trim().length < 3) {
      setError("Give a reason — it is recorded in the audit trail.");
      return;
    }

    const body: Record<string, unknown> = { reason: reason.trim() };
    if (copy.needsClass) body.class_id = classId;
    if (!copy.needsClass && effectiveDate) body.effective_date = effectiveDate;
    if (action === "readmit" && effectiveDate) body.effective_date = effectiveDate;

    setSaving(true);
    setError("");
    try {
      const res = await api<{ data: LifecycleResult }>(
        `/api/v1/academic/students/${studentId}/${action}`,
        { method: "POST", body: JSON.stringify(body) }
      );
      onDone(res.data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not complete this change. Please try again."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalBackdrop
      open
      labelledBy="student-lifecycle-title"
      disableClose={saving}
      onClose={onClose}
    >
      <div className="gw-modal" onClick={(e) => e.stopPropagation()}>
        <header className="gw-modal-header">
          <div>
            <h2 id="student-lifecycle-title" className="gw-modal-title">
              {copy.title}
            </h2>
            <p className="gw-modal-subtitle">{copy.subtitle}</p>
          </div>
          <button
            type="button"
            className="btn btn-ghost gw-modal-close"
            onClick={onClose}
            disabled={saving}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </header>

        <form className="gw-modal-body" onSubmit={handleSubmit}>
          {error && (
            <div className="gw-alert gw-alert-error" role="alert">
              {error}
            </div>
          )}

          <div className="gw-alert gw-alert-info">
            {copy.destructive ? (
              <>
                <strong>{studentName}</strong> will be removed from the active roll. Any
                unpaid fees stay on record and are not cleared.
              </>
            ) : (
              <>
                This applies to <strong>{studentName}</strong>.
              </>
            )}
          </div>

          <div className="gw-form-grid">
            {copy.needsClass && (
              <Field label="Class" required>
                <AppSelect
                  variant="field"
                  value={classId}
                  onChange={setClassId}
                  aria-label="Class"
                  placeholder="Select class…"
                  options={classOptions}
                />
              </Field>
            )}
            {(copy.destructive || action === "mark-alumni" || action === "readmit") && (
              <Field label="Effective date">
                <input
                  type="date"
                  className="form-input"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                />
              </Field>
            )}
            <Field label="Reason" required>
              <input
                className="form-input"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Recorded in the audit trail"
                autoFocus
              />
            </Field>
          </div>
        </form>

        <footer className="gw-modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            // Destructive actions use the danger token rather than a bespoke
            // button variant — the design system has no btn-danger.
            style={
              copy.destructive
                ? { background: "var(--danger)", borderColor: "var(--danger)" }
                : undefined
            }
            onClick={handleSubmit}
            disabled={saving}
          >
            {saving ? "Saving…" : copy.submit}
          </button>
        </footer>
      </div>
    </ModalBackdrop>
  );
}

export function StudentLifecycleModal({ open, action, ...rest }: Props) {
  // Mount a fresh form per action: remounting resets the fields, so no
  // state-syncing effect is needed when the modal reopens.
  if (!open || !action) return null;
  return <LifecycleForm key={action} action={action} {...rest} />;
}
