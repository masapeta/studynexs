"use client";

import { useEffect } from "react";
import { Mail, X } from "lucide-react";
import { ModalBackdrop } from "@/components/layout/ModalBackdrop";
import { PersonMono } from "@/components/briefing/PersonMono";
import type { StaffDirectoryMember } from "@/components/staff/StaffDirectoryCard";

type StaffProfile = StaffDirectoryMember & {
  role?: string | null;
  department?: string | null;
  employee_id?: string | null;
  experience?: string | null;
};

type Props = {
  member: StaffProfile | null;
  onClose: () => void;
};

function displayText(value: string | null | undefined): string {
  const text = value?.trim();
  return text || "—";
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="gw-detail-field">
      <span className="gw-detail-label">{label}</span>
      <span className="gw-detail-value">{value}</span>
    </div>
  );
}

export function StaffProfileModal({ member, onClose }: Props) {
  useEffect(() => {
    if (!member) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [member, onClose]);

  if (!member) return null;

  const mailHref = member.email ? `mailto:${member.email}` : undefined;

  return (
    <ModalBackdrop open={Boolean(member)} labelledBy="staff-profile-title" onClose={onClose}>
      <div className="gw-modal gw-modal-enquiry" onClick={(e) => e.stopPropagation()}>
        <header className="gw-modal-header">
          <div className="gw-staff-profile-header">
            <PersonMono name={member.name} size={48} className="gw-staff-profile-avatar" />
            <div>
              <h2 id="staff-profile-title" className="gw-modal-title">
                {member.name}
              </h2>
              {member.subtitle && <p className="gw-modal-subtitle">{member.subtitle}</p>}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-ghost gw-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </header>

        <div className="gw-modal-body">
          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Role & assignments</h3>
            <div className="gw-form-grid gw-detail-grid">
              <DetailField label="Subject" value={displayText(member.subject)} />
              <DetailField label="Role" value={displayText(member.role_label)} />
              <DetailField label="Position" value={displayText(member.role)} />
              <DetailField label="Classes" value={displayText(member.classes)} />
              <DetailField label="Department" value={displayText(member.department)} />
              <DetailField label="Experience" value={displayText(member.experience)} />
            </div>
          </section>

          <section className="gw-form-section">
            <h3 className="gw-form-section-title">Contact</h3>
            <div className="gw-form-grid gw-detail-grid">
              <DetailField label="Employee ID" value={displayText(member.employee_id)} />
              <DetailField label="Mobile" value={displayText(member.mobile)} />
              <DetailField label="Email" value={displayText(member.email)} />
            </div>
          </section>
        </div>

        <footer className="gw-modal-footer">
          {mailHref ? (
            <a href={mailHref} className="btn btn-outline gw-staff-profile-email">
              <Mail size={16} strokeWidth={2} />
              Email
            </a>
          ) : null}
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </footer>
      </div>
    </ModalBackdrop>
  );
}
