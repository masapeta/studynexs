import type { AdmissionCandidate } from "@/components/admissions/types";

export type AppliedDetails = {
  application_date: string;
  birth_certificate_file_id: string;
  birth_certificate_file_name: string;
  birth_certificate_number: string;
  aadhaar_file_id: string;
  aadhaar_file_name: string;
  aadhaar_number: string;
  apaar_file_id: string;
  apaar_file_name: string;
  apaar_number: string;
  report_card_file_id: string;
  report_card_file_name: string;
  preferred_joining_date: string;
  sibling_in_school: boolean;
  sibling_details: string;
  application_notes: string;
};

export type InterviewDetails = {
  exam_date: string;
  exam_time: string;
  exam_venue: string;
  exam_type: string;
  schedule_notes: string;
};

export type OfferDetails = {
  exam_marks: string;
  max_marks: string;
  merit_result: string;
  recommended_for_offer: boolean;
  merit_notes: string;
  admission_fee: string;
  annual_school_fee: string;
  transport_fee: string;
  hostel_fee: string;
  books_uniform_fee: string;
  other_fees: string;
  fee_agreement_date: string;
  parent_agreed: boolean;
  fee_notes: string;
};

export type EnrolledDetails = {
  tc_received: boolean;
  tc_number: string;
  tc_issue_date: string;
  admission_fee_paid: boolean;
  payment_reference: string;
  enrollment_date: string;
  provisional_admission_no: string;
  enrollment_notes: string;
};

export type StageDetailsMap = {
  applied?: AppliedDetails;
  interview?: InterviewDetails;
  offer?: OfferDetails;
  enrolled?: EnrolledDetails;
};

export const STAGES = ["enquiry", "applied", "interview", "offer", "enrolled"] as const;
export type Stage = (typeof STAGES)[number];

export type StageFormTarget = "applied" | "interview" | "offer" | "enrolled";

export function stageRequiresForm(to: Stage): to is StageFormTarget {
  return to === "applied" || to === "interview" || to === "offer" || to === "enrolled";
}

export function isAdjacentStage(from: Stage, to: Stage): boolean {
  if (from === to) return false;
  return Math.abs(STAGES.indexOf(to) - STAGES.indexOf(from)) === 1;
}

export function canMoveToStage(from: Stage, to: Stage): boolean {
  return isAdjacentStage(from, to);
}

function hasAnyLaterStageDetails(
  candidate: AdmissionCandidate,
  targetStage: StageFormTarget
): boolean {
  const targetIdx = STAGES.indexOf(targetStage);
  for (let i = targetIdx + 1; i < STAGES.length; i++) {
    const key = STAGES[i];
    if (key === "enquiry") continue;
    const stored = candidate.stage_details?.[key] as Record<string, unknown> | undefined;
    if (stored && typeof stored === "object" && Object.keys(stored).length > 0) {
      return true;
    }
  }
  return false;
}

function hasCompleteAppliedDetails(
  stored: Record<string, unknown> | undefined,
  candidate?: AdmissionCandidate
): boolean {
  if (!stored) return false;
  const aadhaar = String(
    stored.aadhaar_number || candidate?.aadhaar_number || ""
  ).replace(/\D/g, "");
  const birthCertNo = String(
    stored.birth_certificate_number || candidate?.birth_certificate_number || ""
  ).trim();
  return Boolean(
    stored.application_date &&
      stored.birth_certificate_file_id &&
      stored.aadhaar_file_id &&
      birthCertNo &&
      aadhaar.length === 12
  );
}

function hasMinimalStageDetails(
  stored: Record<string, unknown>,
  stage: StageFormTarget,
  candidate?: AdmissionCandidate
): boolean {
  if (stage === "applied") return hasCompleteAppliedDetails(stored, candidate);
  if (stage === "interview") return Boolean(stored.exam_date);
  if (stage === "offer") {
    return stored.exam_marks != null && stored.exam_marks !== "" && stored.admission_fee != null;
  }
  if (stage === "enrolled") {
    return Boolean(stored.tc_number && stored.enrollment_date);
  }
  return Object.keys(stored).length > 0;
}

export function hasStageDetails(
  candidate: AdmissionCandidate,
  stage: StageFormTarget
): boolean {
  // Already completed a later stage — details for this stage were saved earlier.
  if (hasAnyLaterStageDetails(candidate, stage)) return true;

  const stored = candidate.stage_details?.[stage] as Record<string, unknown> | undefined;
  if (!stored || typeof stored !== "object" || Object.keys(stored).length === 0) {
    return false;
  }
  return hasMinimalStageDetails(stored, stage, candidate);
}

export function hasPartialStageDetails(
  candidate: AdmissionCandidate,
  stage: StageFormTarget
): boolean {
  const stored = candidate.stage_details?.[stage] as Record<string, unknown> | undefined;
  return Boolean(stored && typeof stored === "object" && Object.keys(stored).length > 0);
}

export function needsStageForm(
  candidate: AdmissionCandidate,
  target: Stage
): target is StageFormTarget {
  return stageRequiresForm(target) && !hasStageDetails(candidate, target);
}

export function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export const EMPTY_APPLIED: AppliedDetails = {
  application_date: todayIso(),
  birth_certificate_file_id: "",
  birth_certificate_file_name: "",
  birth_certificate_number: "",
  aadhaar_file_id: "",
  aadhaar_file_name: "",
  aadhaar_number: "",
  apaar_file_id: "",
  apaar_file_name: "",
  apaar_number: "",
  report_card_file_id: "",
  report_card_file_name: "",
  preferred_joining_date: "",
  sibling_in_school: false,
  sibling_details: "",
  application_notes: "",
};

export const EMPTY_INTERVIEW: InterviewDetails = {
  exam_date: todayIso(),
  exam_time: "",
  exam_venue: "",
  exam_type: "both",
  schedule_notes: "",
};

export const EMPTY_OFFER: OfferDetails = {
  exam_marks: "",
  max_marks: "100",
  merit_result: "pass",
  recommended_for_offer: false,
  merit_notes: "",
  admission_fee: "",
  annual_school_fee: "",
  transport_fee: "",
  hostel_fee: "",
  books_uniform_fee: "",
  other_fees: "",
  fee_agreement_date: todayIso(),
  parent_agreed: false,
  fee_notes: "",
};

export const EMPTY_ENROLLED: EnrolledDetails = {
  tc_received: false,
  tc_number: "",
  tc_issue_date: "",
  admission_fee_paid: false,
  payment_reference: "",
  enrollment_date: todayIso(),
  provisional_admission_no: "",
  enrollment_notes: "",
};

export function buildAppliedPayload(form: AppliedDetails) {
  const aadhaar = form.aadhaar_number.replace(/\D/g, "");
  const apaar = form.apaar_number.replace(/\D/g, "");
  return {
    application_date: form.application_date,
    birth_certificate_file_id: form.birth_certificate_file_id,
    birth_certificate_file_name: form.birth_certificate_file_name.trim() || null,
    birth_certificate_number: form.birth_certificate_number.trim().toUpperCase(),
    aadhaar_file_id: form.aadhaar_file_id,
    aadhaar_file_name: form.aadhaar_file_name.trim() || null,
    aadhaar_number: aadhaar,
    apaar_file_id: form.apaar_file_id || null,
    apaar_file_name: form.apaar_file_name.trim() || null,
    apaar_number: apaar || null,
    report_card_file_id: form.report_card_file_id || null,
    report_card_file_name: form.report_card_file_name.trim() || null,
    preferred_joining_date: form.preferred_joining_date || null,
    sibling_in_school: form.sibling_in_school,
    sibling_details: form.sibling_details.trim() || null,
    application_notes: form.application_notes.trim() || null,
  };
}

export function buildInterviewPayload(form: InterviewDetails) {
  return {
    exam_date: form.exam_date,
    exam_time: form.exam_time.trim() || null,
    exam_venue: form.exam_venue.trim() || null,
    exam_type: form.exam_type,
    schedule_notes: form.schedule_notes.trim() || null,
  };
}

export function buildOfferPayload(form: OfferDetails) {
  return {
    exam_marks: Number(form.exam_marks),
    max_marks: Number(form.max_marks || 100),
    merit_result: form.merit_result,
    recommended_for_offer: form.recommended_for_offer,
    merit_notes: form.merit_notes.trim() || null,
    admission_fee: Number(form.admission_fee),
    annual_school_fee: Number(form.annual_school_fee),
    transport_fee: Number(form.transport_fee || 0),
    hostel_fee: Number(form.hostel_fee || 0),
    books_uniform_fee: Number(form.books_uniform_fee || 0),
    other_fees: Number(form.other_fees || 0),
    fee_agreement_date: form.fee_agreement_date,
    parent_agreed: form.parent_agreed,
    fee_notes: form.fee_notes.trim() || null,
  };
}

export function buildEnrolledPayload(form: EnrolledDetails) {
  return {
    tc_received: form.tc_received,
    tc_number: form.tc_number.trim(),
    tc_issue_date: form.tc_issue_date || null,
    admission_fee_paid: form.admission_fee_paid,
    payment_reference: form.payment_reference.trim() || null,
    enrollment_date: form.enrollment_date,
    provisional_admission_no: form.provisional_admission_no.trim() || null,
    enrollment_notes: form.enrollment_notes.trim() || null,
  };
}


export function appliedFromStored(
  data?: Record<string, unknown>,
  candidate?: Pick<
    AdmissionCandidate,
    "aadhaar_number" | "birth_certificate_number" | "apaar_number"
  >
): AppliedDetails {
  if (!data) {
    return {
      ...EMPTY_APPLIED,
      application_date: todayIso(),
      birth_certificate_number: candidate?.birth_certificate_number || "",
      aadhaar_number: candidate?.aadhaar_number || "",
      apaar_number: candidate?.apaar_number || "",
    };
  }
  const d = data;
  return {
    application_date: String(d.application_date || todayIso()).slice(0, 10),
    birth_certificate_file_id: d.birth_certificate_file_id
      ? String(d.birth_certificate_file_id)
      : "",
    birth_certificate_file_name: d.birth_certificate_file_name
      ? String(d.birth_certificate_file_name)
      : "",
    birth_certificate_number: d.birth_certificate_number
      ? String(d.birth_certificate_number)
      : candidate?.birth_certificate_number || "",
    aadhaar_file_id: d.aadhaar_file_id ? String(d.aadhaar_file_id) : "",
    aadhaar_file_name: d.aadhaar_file_name ? String(d.aadhaar_file_name) : "",
    aadhaar_number: d.aadhaar_number
      ? String(d.aadhaar_number)
      : candidate?.aadhaar_number || "",
    apaar_file_id: d.apaar_file_id ? String(d.apaar_file_id) : "",
    apaar_file_name: d.apaar_file_name ? String(d.apaar_file_name) : "",
    apaar_number: d.apaar_number ? String(d.apaar_number) : candidate?.apaar_number || "",
    report_card_file_id: d.report_card_file_id ? String(d.report_card_file_id) : "",
    report_card_file_name: d.report_card_file_name ? String(d.report_card_file_name) : "",
    preferred_joining_date: d.preferred_joining_date
      ? String(d.preferred_joining_date).slice(0, 10)
      : "",
    sibling_in_school: Boolean(d.sibling_in_school),
    sibling_details: d.sibling_details ? String(d.sibling_details) : "",
    application_notes: d.application_notes ? String(d.application_notes) : "",
  };
}

export function interviewFromStored(data?: Record<string, unknown>): InterviewDetails {
  if (!data) return { ...EMPTY_INTERVIEW, exam_date: todayIso() };
  return {
    exam_date: String(data.exam_date || todayIso()).slice(0, 10),
    exam_time: data.exam_time ? String(data.exam_time) : "",
    exam_venue: data.exam_venue ? String(data.exam_venue) : "",
    exam_type: data.exam_type ? String(data.exam_type) : "both",
    schedule_notes: data.schedule_notes ? String(data.schedule_notes) : "",
  };
}

export function offerFromStored(data?: Record<string, unknown>): OfferDetails {
  if (!data) return { ...EMPTY_OFFER, fee_agreement_date: todayIso() };
  const d = data;
  return {
    exam_marks: d.exam_marks != null ? String(d.exam_marks) : "",
    max_marks: d.max_marks != null ? String(d.max_marks) : "100",
    merit_result: d.merit_result ? String(d.merit_result) : "pass",
    recommended_for_offer: Boolean(d.recommended_for_offer),
    merit_notes: d.merit_notes ? String(d.merit_notes) : "",
    admission_fee: d.admission_fee != null ? String(d.admission_fee) : "",
    annual_school_fee: d.annual_school_fee != null ? String(d.annual_school_fee) : "",
    transport_fee: d.transport_fee != null ? String(d.transport_fee) : "",
    hostel_fee: d.hostel_fee != null ? String(d.hostel_fee) : "",
    books_uniform_fee: d.books_uniform_fee != null ? String(d.books_uniform_fee) : "",
    other_fees: d.other_fees != null ? String(d.other_fees) : "",
    fee_agreement_date: String(d.fee_agreement_date || todayIso()).slice(0, 10),
    parent_agreed: Boolean(d.parent_agreed),
    fee_notes: d.fee_notes ? String(d.fee_notes) : "",
  };
}

export function enrolledFromStored(data?: Record<string, unknown>): EnrolledDetails {
  if (!data) return { ...EMPTY_ENROLLED, enrollment_date: todayIso() };
  const d = data;
  return {
    tc_received: Boolean(d.tc_received),
    tc_number: d.tc_number ? String(d.tc_number) : "",
    tc_issue_date: d.tc_issue_date ? String(d.tc_issue_date).slice(0, 10) : "",
    admission_fee_paid: Boolean(d.admission_fee_paid),
    payment_reference: d.payment_reference ? String(d.payment_reference) : "",
    enrollment_date: String(d.enrollment_date || todayIso()).slice(0, 10),
    provisional_admission_no: d.provisional_admission_no
      ? String(d.provisional_admission_no)
      : "",
    enrollment_notes: d.enrollment_notes ? String(d.enrollment_notes) : "",
  };
}

export const MERIT_LABELS: Record<string, string> = {
  pass: "Pass",
  merit: "Merit",
  waitlist: "Waitlist",
  fail: "Fail",
};

export const EXAM_TYPE_LABELS: Record<string, string> = {
  written: "Written test",
  interview: "Interview",
  both: "Written + interview",
};
