"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { UserPlus } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import {
  StaffDirectoryCard,
  type StaffDirectoryMember,
} from "@/components/staff/StaffDirectoryCard";
import {
  StaffOnboardModal,
  type StaffOnboardFormData,
} from "@/components/staff/StaffOnboardModal";
import { StaffProfileModal } from "@/components/staff/StaffProfileModal";

type StaffMember = StaffDirectoryMember & {
  staff_category?: string;
};

const FILTERS = [
  { key: "all", label: "All staff" },
  { key: "homeroom", label: "Homeroom" },
  { key: "subject_teacher", label: "Subject teachers" },
  { key: "admin", label: "Admin" },
] as const;

function buildOnboardPayload(form: StaffOnboardFormData) {
  const aadhaar = form.aadhaar_number.replace(/\D/g, "");
  return {
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim(),
    date_of_birth: form.date_of_birth || null,
    gender: form.gender || null,
    mobile: form.mobile.trim(),
    email: form.email.trim() || null,
    address_line: form.address_line.trim() || null,
    city: form.city.trim() || null,
    role: form.role,
    employee_id: form.employee_id.trim() || null,
    department: form.department.trim() || null,
    qualification: form.qualification.trim() || null,
    joining_date: form.joining_date || null,
    previous_experience: form.previous_experience.trim() || null,
    aadhaar_number: aadhaar.length === 12 ? aadhaar : null,
    aadhaar_document_file_id: form.aadhaar_document_file_id || null,
    experience_document_file_id: form.experience_document_file_id || null,
  };
}

export default function StaffPage() {
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalError, setModalError] = useState("");
  const [saving, setSaving] = useState(false);
  const [profileMember, setProfileMember] = useState<StaffMember | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api<{ data: { staff: StaffMember[]; count: number } }>(
        "/api/v1/ops/staff-directory"
      );
      setStaff(res.data?.staff || []);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load staff"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    let list = staff;
    if (filter !== "all") {
      list = list.filter((s) => s.staff_category === filter);
    }
    const q = searchQuery.trim().toLowerCase();
    if (!q) return list;
    return list.filter((s) => {
      const hay = [
        s.name,
        s.role,
        s.department,
        s.email,
        s.mobile,
        s.subject,
        s.role_label,
        s.classes,
        s.subtitle,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [staff, filter, searchQuery]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: staff.length };
    staff.forEach((s) => {
      const cat = s.staff_category || "admin";
      c[cat] = (c[cat] || 0) + 1;
    });
    return c;
  }, [staff]);

  async function onboardStaff(form: StaffOnboardFormData) {
    setSaving(true);
    setModalError("");
    try {
      await api("/api/v1/ops/staff/onboard", {
        method: "POST",
        body: JSON.stringify(buildOnboardPayload(form)),
      });
      setModalOpen(false);
      await load();
    } catch (e) {
      setModalError(getApiErrorMessage(e, "Failed to onboard staff member"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageShell
      title="Staff & HR"
      subtitle="Staff directory, assignments, and roles"
      action={
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <input
            className="form-input"
            placeholder="Search staff..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: 260 }}
            aria-label="Search staff"
          />
          <button
            type="button"
            className="gw-table-icon-btn"
            aria-label="Onboard staff"
            title="Onboard staff"
            onClick={() => {
              setModalOpen(true);
              setModalError("");
            }}
          >
            <UserPlus size={20} />
          </button>
        </div>
      }
    >
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="gw-pipeline" role="tablist" aria-label="Filter by staff category">
        {FILTERS.map((f) => {
          const active = filter === f.key;
          const count = f.key === "all" ? counts.all || 0 : counts[f.key] || 0;
          return (
            <button
              key={f.key}
              type="button"
              role="tab"
              aria-selected={active}
              className={`gw-pipeline-stage${active ? " gw-pipeline-stage-active" : ""}`}
              onClick={() => setFilter(f.key)}
            >
              <span className="gw-pipeline-count">{count}</span>
              <span className="gw-pipeline-label">{f.label}</span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="gw-center" style={{ padding: 60 }}>
          <div className="spinner" />
        </div>
      ) : filtered.length === 0 ? (
        <p className="gw-muted">
          {searchQuery.trim()
            ? `No staff match "${searchQuery.trim()}".`
            : "No staff in this category."}
        </p>
      ) : (
        <div className="gw-staff-grid">
          {filtered.map((s) => (
            <StaffDirectoryCard
              key={s.id}
              member={s}
              onProfileClick={setProfileMember}
            />
          ))}
        </div>
      )}

      <StaffOnboardModal
        open={modalOpen}
        saving={saving}
        error={modalError}
        onClose={() => !saving && setModalOpen(false)}
        onSubmit={onboardStaff}
      />

      <StaffProfileModal
        member={profileMember}
        onClose={() => setProfileMember(null)}
      />
    </PageShell>
  );
}
