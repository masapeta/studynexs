import { Eye, Mail } from "lucide-react";
import { PersonMono } from "@/components/briefing/PersonMono";

export type StaffDirectoryMember = {
  id: string;
  name: string;
  email?: string | null;
  mobile?: string | null;
  subtitle?: string | null;
  subject?: string | null;
  role_label?: string | null;
  classes?: string | null;
  role?: string | null;
  department?: string | null;
  employee_id?: string | null;
  experience?: string | null;
};

type Props = {
  member: StaffDirectoryMember;
  onProfileClick?: (member: StaffDirectoryMember) => void;
};

export function StaffDirectoryCard({ member, onProfileClick }: Props) {
  const mailHref = member.email ? `mailto:${member.email}` : undefined;

  return (
    <article className="gw-card gw-staff-tile">
      <header className="gw-staff-tile-header">
        <PersonMono name={member.name} size={40} className="gw-staff-tile-avatar" />
        <div className="gw-staff-tile-heading">
          <h3 className="gw-staff-tile-name">{member.name}</h3>
          {member.subtitle && (
            <p className="gw-staff-tile-subtitle">{member.subtitle}</p>
          )}
        </div>
      </header>

      <dl className="gw-staff-tile-meta">
        <div className="gw-staff-tile-row">
          <dt>Subject</dt>
          <dd>
            <span className="gw-staff-tile-subject">{member.subject || "—"}</span>
          </dd>
        </div>
        <div className="gw-staff-tile-row">
          <dt>Role</dt>
          <dd>{member.role_label || "—"}</dd>
        </div>
        <div className="gw-staff-tile-row">
          <dt>Classes</dt>
          <dd>{member.classes || "—"}</dd>
        </div>
      </dl>

      <footer className="gw-staff-tile-footer">
        <button
          type="button"
          className="gw-staff-tile-profile"
          aria-label={`View ${member.name} profile`}
          onClick={() => onProfileClick?.(member)}
        >
          <Eye size={15} strokeWidth={2} />
          Profile
        </button>
        {mailHref ? (
          <a
            href={mailHref}
            className="gw-staff-tile-email"
            aria-label={`Email ${member.name}`}
            title={member.email || undefined}
          >
            <Mail size={16} strokeWidth={2} />
          </a>
        ) : (
          <span className="gw-staff-tile-email gw-staff-tile-email--disabled" aria-hidden>
            <Mail size={16} strokeWidth={2} />
          </span>
        )}
      </footer>
    </article>
  );
}
