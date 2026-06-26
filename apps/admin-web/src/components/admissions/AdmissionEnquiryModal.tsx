"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ModalBackdrop } from "@/components/layout/ModalBackdrop";
import { AppSelect } from "@/components/ui/AppSelect";

export type EnquiryFormData = {
  name: string;
  date_of_birth: string;
  gender: string;
  grade_applied: string;
  enquiry_date: string;
  parent_name: string;
  parent_relation: string;
  parent_occupation: string;
  parent_mobile: string;
  parent_email: string;
  address_line: string;
  city: string;
  previous_school_name: string;
  previous_grade: string;
  enquiry_source: string;
  notes: string;
};

export const EMPTY_ENQUIRY_FORM: EnquiryFormData = {
  name: "",
  date_of_birth: "",
  gender: "",
  grade_applied: "",
  enquiry_date: new Date().toISOString().slice(0, 10),
  parent_name: "",
  parent_relation: "father",
  parent_occupation: "",
  parent_mobile: "",
  parent_email: "",
  address_line: "",
  city: "",
  previous_school_name: "",
  previous_grade: "",
  enquiry_source: "walk_in",
  notes: "",
};

type Props = {
  open: boolean;
  saving: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (data: EnquiryFormData) => void;
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

export function AdmissionEnquiryModal({ open, saving, error, onClose, onSubmit }: Props) {
  const [form, setForm] = useState<EnquiryFormData>(EMPTY_ENQUIRY_FORM);
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (!open) return;
    setForm(EMPTY_ENQUIRY_FORM);
    setLocalError("");
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !saving) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, saving, onClose]);

  if (!open) return null;

  function update<K extends keyof EnquiryFormData>(key: K, value: EnquiryFormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setLocalError("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) {
      setLocalError("Student name is required.");
      return;
    }
    if (!form.grade_applied.trim()) {
      setLocalError("Grade applying for is required.");
      return;
    }
    if (!form.parent_name.trim()) {
      setLocalError("Parent / guardian name is required.");
      return;
    }
    const digits = form.parent_mobile.replace(/\D/g, "");
    if (digits.length < 10) {
      setLocalError("Enter a valid parent mobile number (at least 10 digits).");
      return;
    }
    onSubmit(form);
  }

  const displayError = localError || error;

  return (
    <ModalBackdrop
      open={open}
      labelledBy="admission-enquiry-title"
      disableClose={saving}
      onClose={onClose}
    >
      <div className="gw-modal gw-modal-enquiry" onClick={(e) => e.stopPropagation()}>
        <header className="gw-modal-header">
          <div>
            <h2 id="admission-enquiry-title" className="gw-modal-title">
              New admission enquiry
            </h2>
            <p className="gw-modal-subtitle">
              Capture student, parent, and previous school details.
            </p>
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
          {displayError && <div className="gw-alert gw-alert-error">{displayError}</div>}

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Student details</h3>
            <div className="gw-form-grid">
              <Field label="Student name" required>
                <input
                  className="form-input"
                  value={form.name}
                  onChange={(e) => update("name", e.target.value)}
                  placeholder="Full name"
                  autoFocus
                />
              </Field>
              <Field label="Date of birth">
                <input
                  type="date"
                  className="form-input"
                  value={form.date_of_birth}
                  onChange={(e) => update("date_of_birth", e.target.value)}
                />
              </Field>
              <Field label="Gender">
                <AppSelect
                  variant="field"
                  value={form.gender}
                  onChange={(v) => update("gender", v)}
                  aria-label="Gender"
                  placeholder="Select"
                  options={[
                    { value: "", label: "Select" },
                    { value: "male", label: "Male" },
                    { value: "female", label: "Female" },
                    { value: "other", label: "Other" },
                  ]}
                />
              </Field>
              <Field label="Grade applying for" required>
                <input
                  className="form-input"
                  value={form.grade_applied}
                  onChange={(e) => update("grade_applied", e.target.value)}
                  placeholder="e.g. 6"
                />
              </Field>
              <Field label="Enquiry date" required>
                <input
                  type="date"
                  className="form-input"
                  value={form.enquiry_date}
                  onChange={(e) => update("enquiry_date", e.target.value)}
                />
              </Field>
              <Field label="How did they hear about us?">
                <AppSelect
                  variant="field"
                  value={form.enquiry_source}
                  onChange={(v) => update("enquiry_source", v)}
                  aria-label="Enquiry source"
                  options={[
                    { value: "walk_in", label: "Walk-in" },
                    { value: "referral", label: "Referral" },
                    { value: "website", label: "Website" },
                    { value: "phone", label: "Phone call" },
                    { value: "social", label: "Social media" },
                    { value: "other", label: "Other" },
                  ]}
                />
              </Field>
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Parent / guardian</h3>
            <div className="gw-form-grid">
              <Field label="Parent / guardian name" required>
                <input
                  className="form-input"
                  value={form.parent_name}
                  onChange={(e) => update("parent_name", e.target.value)}
                  placeholder="Full name"
                />
              </Field>
              <Field label="Relationship">
                <AppSelect
                  variant="field"
                  value={form.parent_relation}
                  onChange={(v) => update("parent_relation", v)}
                  aria-label="Parent relationship"
                  options={[
                    { value: "father", label: "Father" },
                    { value: "mother", label: "Mother" },
                    { value: "guardian", label: "Guardian" },
                  ]}
                />
              </Field>
              <Field label="Occupation">
                <input
                  className="form-input"
                  value={form.parent_occupation}
                  onChange={(e) => update("parent_occupation", e.target.value)}
                  placeholder="e.g. Engineer, Teacher"
                />
              </Field>
              <Field label="Mobile" required>
                <input
                  className="form-input"
                  type="tel"
                  value={form.parent_mobile}
                  onChange={(e) => update("parent_mobile", e.target.value)}
                  placeholder="10-digit mobile"
                />
              </Field>
              <Field label="Email">
                <input
                  className="form-input"
                  type="email"
                  value={form.parent_email}
                  onChange={(e) => update("parent_email", e.target.value)}
                  placeholder="parent@email.com"
                />
              </Field>
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Address</h3>
            <div className="gw-form-grid">
              <Field label="Address">
                <input
                  className="form-input"
                  value={form.address_line}
                  onChange={(e) => update("address_line", e.target.value)}
                  placeholder="House no., street, area"
                />
              </Field>
              <Field label="City">
                <input
                  className="form-input"
                  value={form.city}
                  onChange={(e) => update("city", e.target.value)}
                  placeholder="City"
                />
              </Field>
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Previous school</h3>
            <div className="gw-form-grid">
              <Field label="School name">
                <input
                  className="form-input"
                  value={form.previous_school_name}
                  onChange={(e) => update("previous_school_name", e.target.value)}
                  placeholder="Last school attended"
                />
              </Field>
              <Field label="Last grade completed">
                <input
                  className="form-input"
                  value={form.previous_grade}
                  onChange={(e) => update("previous_grade", e.target.value)}
                  placeholder="e.g. 5"
                />
              </Field>
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Additional notes</h3>
            <Field label="Remarks">
              <textarea
                className="form-input"
                rows={3}
                value={form.notes}
                onChange={(e) => update("notes", e.target.value)}
                placeholder="Sibling in school, special requirements, follow-up date…"
              />
            </Field>
          </section>

          <footer className="gw-modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Add enquiry"}
            </button>
          </footer>
        </form>
      </div>
    </ModalBackdrop>
  );
}
