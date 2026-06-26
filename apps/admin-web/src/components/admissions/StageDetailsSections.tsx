import { inr } from "@/lib/format";
import { formatAdmissionDate, displayText } from "@/components/admissions/types";
import type { StageDetailsMap } from "@/components/admissions/stage-forms";
import { EXAM_TYPE_LABELS, MERIT_LABELS } from "@/components/admissions/stage-forms";
import { AdmissionDocumentLink } from "@/components/admissions/AdmissionDocumentLink";

function yesNo(value: boolean | undefined) {
  if (value === undefined) return "—";
  return value ? "Yes" : "No";
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="gw-detail-field">
      <span className="gw-detail-label">{label}</span>
      <span className="gw-detail-value">{value}</span>
    </div>
  );
}

function DocDetailField({
  label,
  fileId,
  fileName,
}: {
  label: string;
  fileId?: string;
  fileName?: string | null;
}) {
  return (
    <div className="gw-detail-field">
      <span className="gw-detail-label">{label}</span>
      <span className="gw-detail-value">
        {fileId ? (
          <AdmissionDocumentLink fileId={fileId} fileName={fileName} />
        ) : (
          "—"
        )}
      </span>
    </div>
  );
}

export function StageDetailsSections({ details }: { details?: StageDetailsMap }) {
  if (!details) return null;

  const applied = details.applied;
  const interview = details.interview;
  const offer = details.offer;
  const enrolled = details.enrolled;

  if (!applied && !interview && !offer && !enrolled) return null;

  return (
    <>
      {applied && (
        <section className="gw-form-section">
          <h3 className="gw-form-section-title">Application (Enquiry → Applied)</h3>
          <div className="gw-form-grid gw-detail-grid">
            <DetailField
              label="Application date"
              value={formatAdmissionDate(applied.application_date)}
            />
            <DetailField
              label="Preferred joining"
              value={formatAdmissionDate(applied.preferred_joining_date)}
            />
            <DocDetailField
              label="Birth certificate"
              fileId={applied.birth_certificate_file_id}
              fileName={applied.birth_certificate_file_name}
            />
            <DetailField
              label="Birth certificate no."
              value={displayText(applied.birth_certificate_number)}
            />
            <DocDetailField
              label="Aadhaar copy"
              fileId={applied.aadhaar_file_id}
              fileName={applied.aadhaar_file_name}
            />
            <DetailField label="Aadhaar number" value={displayText(applied.aadhaar_number)} />
            <DocDetailField
              label="APAAR ID"
              fileId={applied.apaar_file_id}
              fileName={applied.apaar_file_name}
            />
            <DetailField label="APAAR number" value={displayText(applied.apaar_number)} />
            <DocDetailField
              label="Previous school report card"
              fileId={applied.report_card_file_id}
              fileName={applied.report_card_file_name}
            />
            <DetailField label="Sibling in school" value={yesNo(applied.sibling_in_school)} />
            {applied.sibling_details && (
              <DetailField label="Sibling details" value={displayText(applied.sibling_details)} />
            )}
          </div>
          {applied.application_notes && (
            <div className="gw-detail-field gw-detail-field-full">
              <span className="gw-detail-label">Application notes</span>
              <span className="gw-detail-value">{applied.application_notes}</span>
            </div>
          )}
        </section>
      )}

      {interview && (
        <section className="gw-form-section">
          <h3 className="gw-form-section-title">Exam schedule (Applied → Interview)</h3>
          <div className="gw-form-grid gw-detail-grid">
            <DetailField label="Exam date" value={formatAdmissionDate(interview.exam_date)} />
            <DetailField label="Exam time" value={displayText(interview.exam_time)} />
            <DetailField label="Venue" value={displayText(interview.exam_venue)} />
            <DetailField
              label="Exam type"
              value={EXAM_TYPE_LABELS[interview.exam_type] || interview.exam_type}
            />
          </div>
          {interview.schedule_notes && (
            <div className="gw-detail-field gw-detail-field-full">
              <span className="gw-detail-label">Schedule notes</span>
              <span className="gw-detail-value">{interview.schedule_notes}</span>
            </div>
          )}
        </section>
      )}

      {offer && (
        <section className="gw-form-section">
          <h3 className="gw-form-section-title">Merit & fees (Interview → Offer)</h3>
          <div className="gw-form-grid gw-detail-grid">
            {offer.exam_marks != null && offer.exam_marks !== "" && (
              <>
                <DetailField
                  label="Marks"
                  value={`${offer.exam_marks} / ${offer.max_marks || 100}`}
                />
                <DetailField
                  label="Merit result"
                  value={MERIT_LABELS[offer.merit_result || ""] || offer.merit_result || "—"}
                />
                <DetailField
                  label="Recommended"
                  value={yesNo(offer.recommended_for_offer)}
                />
              </>
            )}
            <DetailField label="Admission fee" value={inr(Number(offer.admission_fee))} />
            <DetailField label="Annual school fee" value={inr(Number(offer.annual_school_fee))} />
            <DetailField label="Transport fee" value={inr(Number(offer.transport_fee || 0))} />
            <DetailField label="Hostel fee" value={inr(Number(offer.hostel_fee || 0))} />
            <DetailField
              label="Books & uniform"
              value={inr(Number(offer.books_uniform_fee || 0))}
            />
            <DetailField label="Other fees" value={inr(Number(offer.other_fees || 0))} />
            <DetailField
              label="Agreement date"
              value={formatAdmissionDate(offer.fee_agreement_date)}
            />
            <DetailField label="Parent agreed" value={yesNo(offer.parent_agreed)} />
          </div>
          {offer.merit_notes && (
            <div className="gw-detail-field gw-detail-field-full">
              <span className="gw-detail-label">Merit notes</span>
              <span className="gw-detail-value">{offer.merit_notes}</span>
            </div>
          )}
          {offer.fee_notes && (
            <div className="gw-detail-field gw-detail-field-full">
              <span className="gw-detail-label">Fee notes</span>
              <span className="gw-detail-value">{offer.fee_notes}</span>
            </div>
          )}
        </section>
      )}

      {enrolled && (
        <section className="gw-form-section">
          <h3 className="gw-form-section-title">Enrollment (Offer → Enrolled)</h3>
          <div className="gw-form-grid gw-detail-grid">
            <DetailField label="TC number" value={displayText(enrolled.tc_number)} />
            <DetailField
              label="TC issue date"
              value={formatAdmissionDate(enrolled.tc_issue_date)}
            />
            <DetailField label="TC received" value={yesNo(enrolled.tc_received)} />
            <DetailField
              label="Admission fee paid"
              value={yesNo(enrolled.admission_fee_paid)}
            />
            <DetailField
              label="Payment reference"
              value={displayText(enrolled.payment_reference)}
            />
            <DetailField
              label="Enrollment date"
              value={formatAdmissionDate(enrolled.enrollment_date)}
            />
            <DetailField
              label="Provisional admission no."
              value={displayText(enrolled.provisional_admission_no)}
            />
          </div>
          {enrolled.enrollment_notes && (
            <div className="gw-detail-field gw-detail-field-full">
              <span className="gw-detail-label">Enrollment notes</span>
              <span className="gw-detail-value">{enrolled.enrollment_notes}</span>
            </div>
          )}
        </section>
      )}
    </>
  );
}
