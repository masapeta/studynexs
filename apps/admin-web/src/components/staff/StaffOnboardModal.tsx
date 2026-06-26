"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ModalBackdrop } from "@/components/layout/ModalBackdrop";
import { AppSelect } from "@/components/ui/AppSelect";
import { DocumentUploadField } from "@/components/admissions/DocumentUploadField";
import { uploadAdmissionDocument } from "@/components/admissions/admission-upload";

export type StaffOnboardFormData = {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  mobile: string;
  email: string;
  address_line: string;
  city: string;
  role: string;
  employee_id: string;
  department: string;
  qualification: string;
  joining_date: string;
  previous_experience: string;
  aadhaar_number: string;
  aadhaar_document_file_id: string;
  aadhaar_document_file_name: string;
  experience_document_file_id: string;
  experience_document_file_name: string;
};

export const EMPTY_STAFF_ONBOARD_FORM: StaffOnboardFormData = {
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "",
  mobile: "",
  email: "",
  address_line: "",
  city: "",
  role: "teacher",
  employee_id: "",
  department: "",
  qualification: "",
  joining_date: new Date().toISOString().slice(0, 10),
  previous_experience: "",
  aadhaar_number: "",
  aadhaar_document_file_id: "",
  aadhaar_document_file_name: "",
  experience_document_file_id: "",
  experience_document_file_name: "",
};

const STAFF_ROLES = [
  { value: "teacher", label: "Subject teacher" },
  { value: "class_incharge", label: "Class incharge (homeroom)" },
  { value: "admin", label: "Admin" },
  { value: "operations", label: "Operations" },
] as const;

type Props = {
  open: boolean;
  saving: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (data: StaffOnboardFormData) => void;
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

export function StaffOnboardModal({ open, saving, error, onClose, onSubmit }: Props) {
  const [form, setForm] = useState<StaffOnboardFormData>(EMPTY_STAFF_ONBOARD_FORM);
  const [localError, setLocalError] = useState("");
  const [uploadingDoc, setUploadingDoc] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setForm(EMPTY_STAFF_ONBOARD_FORM);
    setLocalError("");
    setUploadingDoc(null);
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

  function update<K extends keyof StaffOnboardFormData>(key: K, value: StaffOnboardFormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setLocalError("");
  }

  async function uploadDoc(
    file: File,
    idKey: "aadhaar_document_file_id" | "experience_document_file_id",
    nameKey: "aadhaar_document_file_name" | "experience_document_file_name"
  ) {
    setUploadingDoc(idKey);
    setLocalError("");
    try {
      const { id, name } = await uploadAdmissionDocument(file, "document");
      setForm((prev) => ({ ...prev, [idKey]: id, [nameKey]: name }));
    } catch (e) {
      setLocalError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploadingDoc(null);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.first_name.trim() || !form.last_name.trim()) {
      setLocalError("First name and last name are required.");
      return;
    }
    const digits = form.mobile.replace(/\D/g, "");
    if (digits.length < 10) {
      setLocalError("Enter a valid mobile number (at least 10 digits).");
      return;
    }
    if (form.aadhaar_number.trim()) {
      const aadhaar = form.aadhaar_number.replace(/\D/g, "");
      if (aadhaar.length !== 12) {
        setLocalError("Aadhaar must be 12 digits.");
        return;
      }
    }
    onSubmit(form);
  }

  const displayError = localError || error;
  const docBusy = saving || Boolean(uploadingDoc);

  return (
    <ModalBackdrop
      open={open}
      labelledBy="staff-onboard-title"
      disableClose={saving || Boolean(uploadingDoc)}
      onClose={onClose}
    >
      <div className="gw-modal gw-modal-enquiry" onClick={(e) => e.stopPropagation()}>
        <header className="gw-modal-header">
          <div>
            <h2 id="staff-onboard-title" className="gw-modal-title">
              Onboard staff member
            </h2>
            <p className="gw-modal-subtitle">
              Personal details, employment history, and identity documents.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-ghost gw-modal-close"
            onClick={onClose}
            disabled={docBusy}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </header>

        <form className="gw-modal-body" onSubmit={handleSubmit}>
          {displayError && <div className="gw-alert gw-alert-error">{displayError}</div>}

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Personal details</h3>
            <div className="gw-form-grid">
              <Field label="First name" required>
                <input
                  className="form-input"
                  value={form.first_name}
                  onChange={(e) => update("first_name", e.target.value)}
                  placeholder="First name"
                />
              </Field>
              <Field label="Last name" required>
                <input
                  className="form-input"
                  value={form.last_name}
                  onChange={(e) => update("last_name", e.target.value)}
                  placeholder="Last name"
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
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Contact</h3>
            <div className="gw-form-grid">
              <Field label="Mobile" required>
                <input
                  className="form-input"
                  value={form.mobile}
                  onChange={(e) => update("mobile", e.target.value)}
                  placeholder="+91…"
                />
              </Field>
              <Field label="Email">
                <input
                  type="email"
                  className="form-input"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  placeholder="work@school.edu"
                />
              </Field>
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
            <h3 className="gw-form-section-title">Employment</h3>
            <div className="gw-form-grid">
              <Field label="Role" required>
                <AppSelect
                  variant="field"
                  value={form.role}
                  onChange={(v) => update("role", v)}
                  aria-label="Staff role"
                  options={STAFF_ROLES.map((r) => ({ value: r.value, label: r.label }))}
                />
              </Field>
              <Field label="Employee ID">
                <input
                  className="form-input"
                  value={form.employee_id}
                  onChange={(e) => update("employee_id", e.target.value)}
                  placeholder="e.g. EMP-1042"
                />
              </Field>
              <Field label="Department">
                <input
                  className="form-input"
                  value={form.department}
                  onChange={(e) => update("department", e.target.value)}
                  placeholder="Defaults from role if empty"
                />
              </Field>
              <Field label="Joining date">
                <input
                  type="date"
                  className="form-input"
                  value={form.joining_date}
                  onChange={(e) => update("joining_date", e.target.value)}
                />
              </Field>
              <Field label="Qualification">
                <input
                  className="form-input"
                  value={form.qualification}
                  onChange={(e) => update("qualification", e.target.value)}
                  placeholder="e.g. B.Ed, M.Sc"
                />
              </Field>
            </div>
            <Field label="Previous experience">
              <textarea
                className="form-input"
                rows={3}
                value={form.previous_experience}
                onChange={(e) => update("previous_experience", e.target.value)}
                placeholder="Schools taught at, subjects, years of experience…"
              />
            </Field>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Identity & documents</h3>
            <div className="gw-form-grid">
              <Field label="Aadhaar number">
                <input
                  className="form-input"
                  inputMode="numeric"
                  value={form.aadhaar_number}
                  onChange={(e) => update("aadhaar_number", e.target.value)}
                  placeholder="12-digit Aadhaar"
                  maxLength={14}
                />
              </Field>
            </div>
            <div className="gw-doc-upload-grid">
              <DocumentUploadField
                label="Aadhaar card (scan)"
                fileId={form.aadhaar_document_file_id}
                fileName={form.aadhaar_document_file_name}
                uploading={uploadingDoc === "aadhaar_document_file_id"}
                disabled={docBusy}
                onSelect={(file) => uploadDoc(file, "aadhaar_document_file_id", "aadhaar_document_file_name")}
                onClear={() =>
                  setForm((prev) => ({
                    ...prev,
                    aadhaar_document_file_id: "",
                    aadhaar_document_file_name: "",
                  }))
                }
              />
              <DocumentUploadField
                label="Experience certificate (optional)"
                fileId={form.experience_document_file_id}
                fileName={form.experience_document_file_name}
                uploading={uploadingDoc === "experience_document_file_id"}
                disabled={docBusy}
                onSelect={(file) =>
                  uploadDoc(file, "experience_document_file_id", "experience_document_file_name")
                }
                onClear={() =>
                  setForm((prev) => ({
                    ...prev,
                    experience_document_file_id: "",
                    experience_document_file_name: "",
                  }))
                }
              />
            </div>
          </section>

          <footer className="gw-modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={docBusy}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={docBusy}>
              {saving ? "Onboarding…" : "Onboard staff"}
            </button>
          </footer>
        </form>
      </div>
    </ModalBackdrop>
  );
}
