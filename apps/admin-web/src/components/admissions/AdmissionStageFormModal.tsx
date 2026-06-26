"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ModalBackdrop } from "@/components/layout/ModalBackdrop";
import {
  extractAdmissionDocumentNumber,
  type AdmissionDocumentType,
  uploadAdmissionDocument,
} from "@/components/admissions/admission-upload";
import { DocumentUploadField } from "@/components/admissions/DocumentUploadField";
import { AppSelect } from "@/components/ui/AppSelect";
import { getApiErrorMessage } from "@/lib/api";
import type { AdmissionCandidate } from "@/components/admissions/types";
import { stageLabel } from "@/components/admissions/types";
import {
  type AppliedDetails,
  type EnrolledDetails,
  type InterviewDetails,
  type OfferDetails,
  type StageFormTarget,
  appliedFromStored,
  buildAppliedPayload,
  buildEnrolledPayload,
  buildInterviewPayload,
  buildOfferPayload,
  enrolledFromStored,
  hasPartialStageDetails,
  interviewFromStored,
  offerFromStored,
} from "@/components/admissions/stage-forms";

type Props = {
  candidate: AdmissionCandidate | null;
  targetStage: StageFormTarget | null;
  saving: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (details: Record<string, unknown>) => void;
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

function CheckField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="gw-check-field">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

const TITLES: Record<StageFormTarget, string> = {
  applied: "Application details",
  interview: "Schedule entrance exam",
  offer: "Merit & fee agreement",
  enrolled: "Enrollment checklist",
};

const SUBTITLES: Record<StageFormTarget, string> = {
  applied: "Record documents received and application information before marking as Applied.",
  interview: "Schedule the written test and/or interview before moving to Interview.",
  offer: "Enter exam marks and agreed fees before moving to Offer.",
  enrolled: "Confirm TC, payment, and enrollment details before completing admission.",
};

export function AdmissionStageFormModal({
  candidate,
  targetStage,
  saving,
  error,
  onClose,
  onSubmit,
}: Props) {
  const [localError, setLocalError] = useState("");
  const [applied, setApplied] = useState<AppliedDetails>(appliedFromStored());
  const [interview, setInterview] = useState<InterviewDetails>(interviewFromStored());
  const [offer, setOffer] = useState<OfferDetails>(offerFromStored());
  const [enrolled, setEnrolled] = useState<EnrolledDetails>(enrolledFromStored());
  const [uploadingDoc, setUploadingDoc] = useState<string | null>(null);
  const [extractingDoc, setExtractingDoc] = useState<string | null>(null);

  async function handleDocUpload(
    field:
      | "birth_certificate_file_id"
      | "aadhaar_file_id"
      | "apaar_file_id"
      | "report_card_file_id",
    nameField:
      | "birth_certificate_file_name"
      | "aadhaar_file_name"
      | "apaar_file_name"
      | "report_card_file_name",
    numberField:
      | "birth_certificate_number"
      | "aadhaar_number"
      | "apaar_number"
      | null,
    documentType: AdmissionDocumentType | null,
    file: File,
    category: "document" | "report_card"
  ) {
    setUploadingDoc(field);
    setLocalError("");
    try {
      const uploaded = await uploadAdmissionDocument(file, category);
      setApplied((prev) => ({
        ...prev,
        [field]: uploaded.id,
        [nameField]: uploaded.name,
      }));

      if (numberField && documentType) {
        setExtractingDoc(field);
        try {
          const number = await extractAdmissionDocumentNumber(uploaded.id, documentType);
          if (number) {
            setApplied((prev) => ({ ...prev, [numberField]: number }));
          }
        } catch {
          // User can enter the number manually if auto-detection fails.
        } finally {
          setExtractingDoc(null);
        }
      }
    } catch (e) {
      setLocalError(getApiErrorMessage(e, "Could not upload file"));
    } finally {
      setUploadingDoc(null);
    }
  }

  function clearDoc(
    field:
      | "birth_certificate_file_id"
      | "aadhaar_file_id"
      | "apaar_file_id"
      | "report_card_file_id",
    nameField:
      | "birth_certificate_file_name"
      | "aadhaar_file_name"
      | "apaar_file_name"
      | "report_card_file_name",
    numberField:
      | "birth_certificate_number"
      | "aadhaar_number"
      | "apaar_number"
      | null
  ) {
    setApplied((prev) => ({
      ...prev,
      [field]: "",
      [nameField]: "",
      ...(numberField ? { [numberField]: "" } : {}),
    }));
  }

  useEffect(() => {
    if (!candidate || !targetStage) return;
    setLocalError("");
    const stored = candidate.stage_details?.[targetStage] as Record<string, unknown> | undefined;
    if (targetStage === "applied") setApplied(appliedFromStored(stored, candidate));
    if (targetStage === "interview") setInterview(interviewFromStored(stored));
    if (targetStage === "offer") setOffer(offerFromStored(stored));
    if (targetStage === "enrolled") setEnrolled(enrolledFromStored(stored));
  }, [candidate, targetStage]);

  useEffect(() => {
    if (!targetStage) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !saving) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [targetStage, saving, onClose]);

  if (!candidate || !targetStage) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError("");

    if (targetStage === "applied") {
      if (!applied.application_date) {
        setLocalError("Application date is required.");
        return;
      }
      if (!applied.birth_certificate_file_id) {
        setLocalError("Upload the birth certificate (required).");
        return;
      }
      if (!applied.birth_certificate_number.trim()) {
        setLocalError("Birth certificate number is required.");
        return;
      }
      if (!applied.aadhaar_file_id) {
        setLocalError("Upload the Aadhaar copy (required).");
        return;
      }
      const aadhaarDigits = applied.aadhaar_number.replace(/\D/g, "");
      if (aadhaarDigits.length !== 12) {
        setLocalError("Aadhaar number must be 12 digits.");
        return;
      }
      if (uploadingDoc || extractingDoc) {
        setLocalError("Wait for the file upload and number detection to finish.");
        return;
      }
      onSubmit(buildAppliedPayload(applied));
      return;
    }

    if (targetStage === "interview") {
      if (!interview.exam_date) {
        setLocalError("Exam date is required.");
        return;
      }
      onSubmit(buildInterviewPayload(interview));
      return;
    }

    if (targetStage === "offer") {
      if (!offer.exam_marks || !offer.max_marks) {
        setLocalError("Exam marks and maximum marks are required.");
        return;
      }
      if (Number(offer.exam_marks) > Number(offer.max_marks)) {
        setLocalError("Marks cannot exceed the maximum.");
        return;
      }
      if (offer.merit_result === "fail") {
        setLocalError("Cannot move to offer with a fail result.");
        return;
      }
      if (!offer.recommended_for_offer) {
        setLocalError("Confirm the candidate is recommended for offer.");
        return;
      }
      if (!offer.admission_fee || !offer.annual_school_fee) {
        setLocalError("Admission fee and annual school fee are required.");
        return;
      }
      if (!offer.parent_agreed) {
        setLocalError("Confirm that the parent agreed to the fee structure.");
        return;
      }
      onSubmit(buildOfferPayload(offer));
      return;
    }

    if (!enrolled.tc_number.trim()) {
      setLocalError("TC number is required.");
      return;
    }
    if (!enrolled.tc_received || !enrolled.admission_fee_paid) {
      setLocalError("Confirm TC received and admission fee paid.");
      return;
    }
    onSubmit(buildEnrolledPayload(enrolled));
  }

  const displayError = localError || error;
  const resumingSavedDetails =
    candidate && targetStage
      ? hasPartialStageDetails(candidate, targetStage)
      : false;

  return (
    <ModalBackdrop
      open={Boolean(candidate && targetStage)}
      labelledBy="admission-stage-form-title"
      disableClose={saving}
      onClose={onClose}
    >
      <div className="gw-modal gw-modal-enquiry" onClick={(e) => e.stopPropagation()}>
        <header className="gw-modal-header">
          <div>
            <h2 id="admission-stage-form-title" className="gw-modal-title">
              {TITLES[targetStage]}
            </h2>
            <p className="gw-modal-subtitle">
              {candidate.name} · moving to {stageLabel(targetStage)}
            </p>
            <p className="gw-modal-subtitle">{SUBTITLES[targetStage]}</p>
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
          {resumingSavedDetails && (
            <div className="gw-alert gw-alert-info">
              Previously saved details are loaded below. Uploaded files are kept — update
              only what changed, or save to continue.
            </div>
          )}

          {targetStage === "applied" && (
            <>
              <section className="gw-form-section">
                <h3 className="gw-form-section-title">Application</h3>
                <div className="gw-form-grid">
                  <Field label="Application date" required>
                    <input
                      type="date"
                      className="form-input"
                      value={applied.application_date}
                      onChange={(e) =>
                        setApplied({ ...applied, application_date: e.target.value })
                      }
                    />
                  </Field>
                  <Field label="Preferred joining date">
                    <input
                      type="date"
                      className="form-input"
                      value={applied.preferred_joining_date}
                      onChange={(e) =>
                        setApplied({ ...applied, preferred_joining_date: e.target.value })
                      }
                    />
                  </Field>
                </div>
              </section>
              <section className="gw-form-section">
                <h3 className="gw-form-section-title">Document uploads</h3>
                <p className="gw-form-hint">
                  PDF or image (JPG, PNG, WebP), max 1 MB. Numbers are read via OCR
                  after upload; enter manually if detection fails.
                </p>
                <div className="gw-doc-upload-grid">
                  <div className="gw-doc-upload-cell">
                    <DocumentUploadField
                      label="Birth certificate"
                      required
                      fileId={applied.birth_certificate_file_id}
                      fileName={applied.birth_certificate_file_name}
                      uploading={uploadingDoc === "birth_certificate_file_id"}
                      disabled={saving}
                      onSelect={(file) =>
                        handleDocUpload(
                          "birth_certificate_file_id",
                          "birth_certificate_file_name",
                          "birth_certificate_number",
                          "birth_certificate",
                          file,
                          "document"
                        )
                      }
                      onClear={() =>
                        clearDoc(
                          "birth_certificate_file_id",
                          "birth_certificate_file_name",
                          "birth_certificate_number"
                        )
                      }
                    />
                    {applied.birth_certificate_file_id && (
                      <Field label="Certificate / registration number" required>
                        <input
                          className="form-input"
                          value={applied.birth_certificate_number}
                          onChange={(e) =>
                            setApplied({
                              ...applied,
                              birth_certificate_number: e.target.value.toUpperCase(),
                            })
                          }
                          placeholder={
                            extractingDoc === "birth_certificate_file_id"
                              ? "Detecting number…"
                              : "Auto-detected or enter manually"
                          }
                          disabled={saving || extractingDoc === "birth_certificate_file_id"}
                        />
                      </Field>
                    )}
                  </div>
                  <div className="gw-doc-upload-cell">
                    <DocumentUploadField
                      label="Aadhaar copy"
                      required
                      fileId={applied.aadhaar_file_id}
                      fileName={applied.aadhaar_file_name}
                      uploading={uploadingDoc === "aadhaar_file_id"}
                      disabled={saving}
                      onSelect={(file) =>
                        handleDocUpload(
                          "aadhaar_file_id",
                          "aadhaar_file_name",
                          "aadhaar_number",
                          "aadhaar",
                          file,
                          "document"
                        )
                      }
                      onClear={() =>
                        clearDoc("aadhaar_file_id", "aadhaar_file_name", "aadhaar_number")
                      }
                    />
                    {applied.aadhaar_file_id && (
                      <Field label="Aadhaar number" required>
                        <input
                          className="form-input"
                          inputMode="numeric"
                          maxLength={14}
                          value={applied.aadhaar_number}
                          onChange={(e) =>
                            setApplied({ ...applied, aadhaar_number: e.target.value })
                          }
                          placeholder={
                            extractingDoc === "aadhaar_file_id"
                              ? "Detecting number…"
                              : "12-digit Aadhaar number"
                          }
                          disabled={saving || extractingDoc === "aadhaar_file_id"}
                        />
                      </Field>
                    )}
                  </div>
                  <div className="gw-doc-upload-cell">
                    <DocumentUploadField
                      label="APAAR ID"
                      fileId={applied.apaar_file_id}
                      fileName={applied.apaar_file_name}
                      uploading={uploadingDoc === "apaar_file_id"}
                      disabled={saving}
                      onSelect={(file) =>
                        handleDocUpload(
                          "apaar_file_id",
                          "apaar_file_name",
                          "apaar_number",
                          "apaar",
                          file,
                          "document"
                        )
                      }
                      onClear={() =>
                        clearDoc("apaar_file_id", "apaar_file_name", "apaar_number")
                      }
                    />
                    {applied.apaar_file_id && (
                      <Field label="APAAR ID number">
                        <input
                          className="form-input"
                          inputMode="numeric"
                          maxLength={12}
                          value={applied.apaar_number}
                          onChange={(e) =>
                            setApplied({ ...applied, apaar_number: e.target.value })
                          }
                          placeholder={
                            extractingDoc === "apaar_file_id"
                              ? "Detecting number…"
                              : "12-digit APAAR ID"
                          }
                          disabled={saving || extractingDoc === "apaar_file_id"}
                        />
                      </Field>
                    )}
                  </div>
                  <DocumentUploadField
                    label="Previous school report card"
                    fileId={applied.report_card_file_id}
                    fileName={applied.report_card_file_name}
                    uploading={uploadingDoc === "report_card_file_id"}
                    disabled={saving}
                    onSelect={(file) =>
                      handleDocUpload(
                        "report_card_file_id",
                        "report_card_file_name",
                        null,
                        null,
                        file,
                        "document"
                      )
                    }
                    onClear={() =>
                      clearDoc("report_card_file_id", "report_card_file_name", null)
                    }
                  />
                </div>
                <div className="gw-check-grid" style={{ marginTop: 12 }}>
                  <CheckField
                    label="Sibling already in this school"
                    checked={applied.sibling_in_school}
                    onChange={(v) => setApplied({ ...applied, sibling_in_school: v })}
                  />
                </div>
                {applied.sibling_in_school && (
                  <Field label="Sibling details">
                    <input
                      className="form-input"
                      value={applied.sibling_details}
                      onChange={(e) =>
                        setApplied({ ...applied, sibling_details: e.target.value })
                      }
                      placeholder="Name and class"
                    />
                  </Field>
                )}
              </section>
              <section className="gw-form-section">
                <Field label="Application notes">
                  <textarea
                    className="form-input"
                    rows={3}
                    value={applied.application_notes}
                    onChange={(e) =>
                      setApplied({ ...applied, application_notes: e.target.value })
                    }
                  />
                </Field>
              </section>
            </>
          )}

          {targetStage === "interview" && (
            <>
              <section className="gw-form-section">
                <h3 className="gw-form-section-title">Exam schedule</h3>
                <div className="gw-form-grid">
                  <Field label="Exam date" required>
                    <input
                      type="date"
                      className="form-input"
                      value={interview.exam_date}
                      onChange={(e) => setInterview({ ...interview, exam_date: e.target.value })}
                    />
                  </Field>
                  <Field label="Exam time">
                    <input
                      type="time"
                      className="form-input"
                      value={interview.exam_time}
                      onChange={(e) => setInterview({ ...interview, exam_time: e.target.value })}
                    />
                  </Field>
                  <Field label="Venue / room">
                    <input
                      className="form-input"
                      value={interview.exam_venue}
                      onChange={(e) => setInterview({ ...interview, exam_venue: e.target.value })}
                      placeholder="e.g. Block A, Room 12"
                    />
                  </Field>
                  <Field label="Exam type" required>
                    <AppSelect
                      variant="field"
                      value={interview.exam_type}
                      onChange={(v) => setInterview({ ...interview, exam_type: v })}
                      aria-label="Exam type"
                      options={[
                        { value: "written", label: "Written test" },
                        { value: "interview", label: "Interview only" },
                        { value: "both", label: "Written + interview" },
                      ]}
                    />
                  </Field>
                </div>
              </section>
              <section className="gw-form-section">
                <Field label="Schedule notes">
                  <textarea
                    className="form-input"
                    rows={3}
                    value={interview.schedule_notes}
                    onChange={(e) =>
                      setInterview({ ...interview, schedule_notes: e.target.value })
                    }
                    placeholder="Materials to bring, reporting time, panel members…"
                  />
                </Field>
              </section>
            </>
          )}

          {targetStage === "offer" && (
            <>
              <section className="gw-form-section">
                <h3 className="gw-form-section-title">Exam merit</h3>
                <div className="gw-form-grid">
                  <Field label="Marks scored" required>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className="form-input"
                      value={offer.exam_marks}
                      onChange={(e) => setOffer({ ...offer, exam_marks: e.target.value })}
                    />
                  </Field>
                  <Field label="Maximum marks" required>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      className="form-input"
                      value={offer.max_marks}
                      onChange={(e) => setOffer({ ...offer, max_marks: e.target.value })}
                    />
                  </Field>
                  <Field label="Merit result" required>
                    <AppSelect
                      variant="field"
                      value={offer.merit_result}
                      onChange={(v) => setOffer({ ...offer, merit_result: v })}
                      aria-label="Merit result"
                      options={[
                        { value: "merit", label: "Merit" },
                        { value: "pass", label: "Pass" },
                        { value: "waitlist", label: "Waitlist" },
                        { value: "fail", label: "Fail" },
                      ]}
                    />
                  </Field>
                </div>
                <CheckField
                  label="Recommended for admission offer"
                  checked={offer.recommended_for_offer}
                  onChange={(v) => setOffer({ ...offer, recommended_for_offer: v })}
                />
                <Field label="Merit notes">
                  <textarea
                    className="form-input"
                    rows={2}
                    value={offer.merit_notes}
                    onChange={(e) => setOffer({ ...offer, merit_notes: e.target.value })}
                    placeholder="Panel comments, strengths, areas to watch…"
                  />
                </Field>
              </section>
              <section className="gw-form-section">
                <h3 className="gw-form-section-title">Agreed fees (₹)</h3>
                <div className="gw-form-grid">
                  <Field label="Admission fee" required>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="form-input"
                      value={offer.admission_fee}
                      onChange={(e) => setOffer({ ...offer, admission_fee: e.target.value })}
                    />
                  </Field>
                  <Field label="Annual school fee" required>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="form-input"
                      value={offer.annual_school_fee}
                      onChange={(e) =>
                        setOffer({ ...offer, annual_school_fee: e.target.value })
                      }
                    />
                  </Field>
                  <Field label="Transport fee">
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="form-input"
                      value={offer.transport_fee}
                      onChange={(e) => setOffer({ ...offer, transport_fee: e.target.value })}
                    />
                  </Field>
                  <Field label="Hostel fee">
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="form-input"
                      value={offer.hostel_fee}
                      onChange={(e) => setOffer({ ...offer, hostel_fee: e.target.value })}
                    />
                  </Field>
                  <Field label="Books & uniform">
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="form-input"
                      value={offer.books_uniform_fee}
                      onChange={(e) =>
                        setOffer({ ...offer, books_uniform_fee: e.target.value })
                      }
                    />
                  </Field>
                  <Field label="Other fees">
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="form-input"
                      value={offer.other_fees}
                      onChange={(e) => setOffer({ ...offer, other_fees: e.target.value })}
                    />
                  </Field>
                  <Field label="Agreement date" required>
                    <input
                      type="date"
                      className="form-input"
                      value={offer.fee_agreement_date}
                      onChange={(e) =>
                        setOffer({ ...offer, fee_agreement_date: e.target.value })
                      }
                    />
                  </Field>
                </div>
              </section>
              <section className="gw-form-section">
                <CheckField
                  label="Parent has agreed to this fee structure"
                  checked={offer.parent_agreed}
                  onChange={(v) => setOffer({ ...offer, parent_agreed: v })}
                />
                <Field label="Fee notes">
                  <textarea
                    className="form-input"
                    rows={3}
                    value={offer.fee_notes}
                    onChange={(e) => setOffer({ ...offer, fee_notes: e.target.value })}
                    placeholder="Installment plan, concessions, transport route…"
                  />
                </Field>
              </section>
            </>
          )}

          {targetStage === "enrolled" && (
            <>
              <section className="gw-form-section">
                <h3 className="gw-form-section-title">Transfer certificate (TC)</h3>
                <div className="gw-form-grid">
                  <Field label="TC number" required>
                    <input
                      className="form-input"
                      value={enrolled.tc_number}
                      onChange={(e) => setEnrolled({ ...enrolled, tc_number: e.target.value })}
                    />
                  </Field>
                  <Field label="TC issue date">
                    <input
                      type="date"
                      className="form-input"
                      value={enrolled.tc_issue_date}
                      onChange={(e) =>
                        setEnrolled({ ...enrolled, tc_issue_date: e.target.value })
                      }
                    />
                  </Field>
                  <Field label="Enrollment date" required>
                    <input
                      type="date"
                      className="form-input"
                      value={enrolled.enrollment_date}
                      onChange={(e) =>
                        setEnrolled({ ...enrolled, enrollment_date: e.target.value })
                      }
                    />
                  </Field>
                  <Field label="Provisional admission no.">
                    <input
                      className="form-input"
                      value={enrolled.provisional_admission_no}
                      onChange={(e) =>
                        setEnrolled({ ...enrolled, provisional_admission_no: e.target.value })
                      }
                    />
                  </Field>
                </div>
                <div className="gw-check-grid">
                  <CheckField
                    label="TC received from previous school"
                    checked={enrolled.tc_received}
                    onChange={(v) => setEnrolled({ ...enrolled, tc_received: v })}
                  />
                  <CheckField
                    label="Admission fee paid"
                    checked={enrolled.admission_fee_paid}
                    onChange={(v) => setEnrolled({ ...enrolled, admission_fee_paid: v })}
                  />
                </div>
                <Field label="Payment reference">
                  <input
                    className="form-input"
                    value={enrolled.payment_reference}
                    onChange={(e) =>
                      setEnrolled({ ...enrolled, payment_reference: e.target.value })
                    }
                    placeholder="Receipt / transaction ID"
                  />
                </Field>
              </section>
              <section className="gw-form-section">
                <Field label="Enrollment notes">
                  <textarea
                    className="form-input"
                    rows={3}
                    value={enrolled.enrollment_notes}
                    onChange={(e) =>
                      setEnrolled({ ...enrolled, enrollment_notes: e.target.value })
                    }
                  />
                </Field>
              </section>
            </>
          )}

          <footer className="gw-modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving || !!uploadingDoc || !!extractingDoc}>
              {saving ? "Saving…" : `Move to ${stageLabel(targetStage)}`}
            </button>
          </footer>
        </form>
      </div>
    </ModalBackdrop>
  );
}
