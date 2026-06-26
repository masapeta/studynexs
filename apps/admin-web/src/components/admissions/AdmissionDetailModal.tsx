"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { ModalBackdrop } from "@/components/layout/ModalBackdrop";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import {
  type AdmissionCandidate,
  displayText,
  formatAdmissionDate,
  genderLabel,
  relationLabel,
  sourceLabel,
  stageLabel,
} from "@/components/admissions/types";
import { StageDetailsSections } from "@/components/admissions/StageDetailsSections";

const stageTone: Record<string, "brass" | "blue" | "gray" | "green"> = {
  enquiry: "brass",
  applied: "blue",
  interview: "brass",
  offer: "blue",
  enrolled: "green",
};

type Props = {
  candidate: AdmissionCandidate | null;
  onClose: () => void;
};

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="gw-detail-field">
      <span className="gw-detail-label">{label}</span>
      <span className="gw-detail-value">{value}</span>
    </div>
  );
}

export function AdmissionDetailModal({ candidate, onClose }: Props) {
  useEffect(() => {
    if (!candidate) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [candidate, onClose]);

  if (!candidate) return null;

  return (
    <ModalBackdrop
      open={Boolean(candidate)}
      labelledBy="admission-detail-title"
      onClose={onClose}
    >
      <div className="gw-modal gw-modal-enquiry" onClick={(e) => e.stopPropagation()}>
        <header className="gw-modal-header">
          <div>
            <h2 id="admission-detail-title" className="gw-modal-title">
              {candidate.name}
            </h2>
            <p className="gw-modal-subtitle">
              Enquiry submitted {formatAdmissionDate(candidate.enquiry_date)}
            </p>
          </div>
          <div className="gw-detail-header-actions">
            <StatusBadge tone={stageTone[candidate.stage] || "gray"}>
              {stageLabel(candidate.stage)}
            </StatusBadge>
            <button
              type="button"
              className="btn btn-ghost gw-modal-close"
              onClick={onClose}
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>
        </header>

        <div className="gw-modal-body">
          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Student details</h3>
            <div className="gw-form-grid gw-detail-grid">
              <DetailField label="Student name" value={displayText(candidate.name)} />
              <DetailField
                label="Date of birth"
                value={formatAdmissionDate(candidate.date_of_birth)}
              />
              <DetailField label="Gender" value={genderLabel(candidate.gender)} />
              <DetailField label="Grade applying for" value={displayText(candidate.grade_applied)} />
              <DetailField
                label="Aadhaar number"
                value={displayText(candidate.aadhaar_number)}
              />
              <DetailField
                label="Birth certificate no."
                value={displayText(candidate.birth_certificate_number)}
              />
              <DetailField label="APAAR ID" value={displayText(candidate.apaar_number)} />
              <DetailField
                label="Enquiry date"
                value={formatAdmissionDate(candidate.enquiry_date)}
              />
              <DetailField
                label="How did they hear about us?"
                value={sourceLabel(candidate.enquiry_source)}
              />
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Parent / guardian</h3>
            <div className="gw-form-grid gw-detail-grid">
              <DetailField label="Parent / guardian name" value={displayText(candidate.parent_name)} />
              <DetailField label="Relationship" value={relationLabel(candidate.parent_relation)} />
              <DetailField
                label="Occupation"
                value={displayText(candidate.parent_occupation)}
              />
              <DetailField label="Mobile" value={displayText(candidate.parent_mobile)} />
              <DetailField label="Email" value={displayText(candidate.parent_email)} />
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Address</h3>
            <div className="gw-form-grid gw-detail-grid">
              <DetailField label="Address" value={displayText(candidate.address_line)} />
              <DetailField label="City" value={displayText(candidate.city)} />
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Previous school</h3>
            <div className="gw-form-grid gw-detail-grid">
              <DetailField
                label="School name"
                value={displayText(candidate.previous_school_name)}
              />
              <DetailField
                label="Last grade completed"
                value={displayText(candidate.previous_grade)}
              />
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Additional notes</h3>
            <div className="gw-detail-field gw-detail-field-full">
              <span className="gw-detail-label">Remarks</span>
              <span className="gw-detail-value">{displayText(candidate.notes)}</span>
            </div>
          </section>

          <StageDetailsSections details={candidate.stage_details} />
        </div>

        <footer className="gw-modal-footer">
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </footer>
      </div>
    </ModalBackdrop>
  );
}
