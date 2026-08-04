"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";
import { ArrowLeft, Phone, Mail, Users, ClipboardCheck, Wallet, Bus, BedDouble, History } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import {
  StudentLifecycleModal,
  type LifecycleAction,
  type LifecycleClassOption,
} from "@/components/students/StudentLifecycleModal";
import TopicMasterySection from "./TopicMasterySection";

type EnrollmentRow = {
  id: string;
  class_id: string;
  academic_year_id: string;
  status: string;
  roll_no: string | null;
  enrolled_on: string | null;
  ended_on: string | null;
  class_name: string | null;
};

const STATUS_BADGE: Record<string, string> = {
  active: "badge-success",
  promoted: "badge-info",
  detained: "badge-warning",
  transferred: "badge-info",
  withdrawn: "badge-warning",
  completed: "badge-info",
};

const sectionH: React.CSSProperties = {
  fontSize: 14, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5,
  color: "var(--text-secondary)", marginTop: 0, marginBottom: 16,
};

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="stat-label">{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

export default function StudentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { permissions } = useAuth();
  const [p, setP] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrollments, setEnrollments] = useState<EnrollmentRow[] | null>(null);
  const [classes, setClasses] = useState<LifecycleClassOption[]>([]);
  const [action, setAction] = useState<LifecycleAction | null>(null);
  const [notice, setNotice] = useState<string>("");
  const [feeNotice, setFeeNotice] = useState<string>("");

  const canManage = Boolean(permissions?.can_manage_students);

  const loadProfile = useCallback(() => {
    if (!id) return;
    api(`/api/v1/academic/students/${id}/profile`)
      .then((r) => setP(r.data))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load student")))
      .finally(() => setLoading(false));
  }, [id]);

  const loadEnrollments = useCallback(() => {
    if (!id) return;
    api<{ data: EnrollmentRow[] }>(`/api/v1/academic/students/${id}/enrollments`)
      .then((r) => setEnrollments(r.data || []))
      .catch(() => setEnrollments([]));
  }, [id]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    loadEnrollments();
  }, [loadEnrollments]);

  useEffect(() => {
    if (!canManage) return;
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => setClasses((r.items || r.data || []) as LifecycleClassOption[]))
      .catch(() => {});
  }, [canManage]);

  function handleLifecycleDone(result: {
    student_status: string;
    fee_review_required: boolean;
    fee_review_note: string | null;
  }) {
    setAction(null);
    setNotice(`Student is now ${result.student_status}.`);
    setFeeNotice(result.fee_review_required ? result.fee_review_note || "" : "");
    loadProfile();
    loadEnrollments();
  }

  if (loading) {
    return <div className="loading-screen" style={{ minHeight: "50vh" }}><div className="spinner" /></div>;
  }
  if (error || !p) {
    return <div className="card" style={{ padding: 24, color: "var(--danger)" }}>{error || "Student not found"}</div>;
  }

  // Older profile payloads had no status field; absent means active.
  const studentStatus: string = p.status || "active";
  const isActive = studentStatus === "active";

  const info: [string, React.ReactNode][] = [
    ["Roll No", p.roll_no], ["Admission No", p.admission_no], ["Class", p.class_name],
    ["Date of Birth", p.date_of_birth], ["Gender", p.gender], ["Blood Group", p.blood_group],
    ["APAAR ID", p.apaar_number], ["Mobile", p.mobile], ["Email", p.email],
  ];
  const shown = info.filter(([, v]) => v);

  return (
    <>
      <button className="btn btn-ghost" onClick={() => router.back()} style={{ width: "auto", padding: "6px 10px", marginBottom: 16 }}>
        <ArrowLeft size={16} /> Back to students
      </button>

      {/* Header */}
      <div className="card" style={{ padding: 24, marginBottom: 24, display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ width: 64, height: 64, borderRadius: "50%", background: "linear-gradient(135deg, var(--accent), var(--accent-dark))", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 26, fontWeight: 700, flexShrink: 0 }}>
          {(p.student_name || "?").charAt(0).toUpperCase()}
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>{p.student_name}</h1>
          <div style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 2 }}>
            {p.class_name} · Adm. {p.admission_no}{p.roll_no ? ` · Roll ${p.roll_no}` : ""}
          </div>
        </div>
        {canManage && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
            {isActive ? (
              <>
                <button className="btn btn-outline btn-sm" onClick={() => setAction("change-class")}>
                  Change class
                </button>
                <button className="btn btn-outline btn-sm" onClick={() => setAction("transfer-out")}>
                  Transfer out
                </button>
                <button className="btn btn-outline btn-sm" onClick={() => setAction("withdraw")}>
                  Withdraw
                </button>
                <button className="btn btn-outline btn-sm" onClick={() => setAction("mark-alumni")}>
                  Mark alumni
                </button>
              </>
            ) : (
              <button className="btn btn-primary btn-sm" onClick={() => setAction("readmit")}>
                Re-admit
              </button>
            )}
          </div>
        )}
      </div>

      {notice && (
        <div className="gw-alert gw-alert-info" style={{ marginBottom: 16 }} role="status">
          {notice}
        </div>
      )}
      {feeNotice && (
        <div
          className="gw-alert gw-alert-error"
          style={{ marginBottom: 16 }}
          role="alert"
        >
          {feeNotice}
        </div>
      )}

      {/* Summary stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
          <div className="stat-icon-container icon-green"><ClipboardCheck size={20} /></div>
          <div><div className="stat-label">Attendance</div><div style={{ fontSize: 24, fontWeight: 700 }}>{p.attendance.percentage != null ? `${p.attendance.percentage}%` : "—"}</div></div>
        </div>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
          <div className="stat-icon-container icon-orange"><Wallet size={20} /></div>
          <div><div className="stat-label">Pending Fees</div><div style={{ fontSize: 24, fontWeight: 700 }}>₹ {Number(p.fees.pending || 0).toLocaleString()}</div></div>
        </div>
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
          <div className="stat-icon-container icon-blue"><Users size={20} /></div>
          <div><div className="stat-label">Guardians</div><div style={{ fontSize: 24, fontWeight: 700 }}>{p.parents.length}</div></div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" }}>
        {/* Personal details */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={sectionH}>Personal Details</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px 20px" }}>
            {shown.map(([k, v]) => (
              <div key={k}>
                <div className="stat-label">{k}</div>
                <div style={{ fontWeight: 600, fontSize: 14, textTransform: k === "Gender" ? "capitalize" : "none" }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Parents / Guardians */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={sectionH}>Parents / Guardians</h2>
          {p.parents.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No guardians linked yet.</div>
          ) : (
            p.parents.map((g: any, i: number) => (
              <div key={i} style={{ padding: "12px 0", borderTop: i ? "1px solid var(--border-light)" : "none" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontWeight: 600 }}>{g.name}</span>
                  <span className="badge badge-info" style={{ textTransform: "capitalize" }}>{g.relationship}</span>
                  {g.is_primary && <span className="badge badge-success">Primary</span>}
                </div>
                <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: 13, color: "var(--text-secondary)", flexWrap: "wrap" }}>
                  {g.mobile && <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}><Phone size={13} /> {g.mobile}</span>}
                  {g.email && <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}><Mail size={13} /> {g.email}</span>}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Enrollment history (DM-3): per-year record, newest first */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={sectionH}>
            <History size={14} style={{ verticalAlign: -2, marginRight: 6 }} />
            Enrollment History
          </h2>
          {enrollments === null ? (
            <div className="spinner" style={{ margin: "0 auto" }} />
          ) : enrollments.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
              No enrollment records yet.
            </div>
          ) : (
            enrollments.map((e, i) => (
              <div
                key={e.id}
                style={{
                  padding: "12px 0",
                  borderTop: i ? "1px solid var(--border-light)" : "none",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  flexWrap: "wrap",
                }}
              >
                <span style={{ fontWeight: 600 }}>{e.class_name || "—"}</span>
                <span
                  className={`badge ${STATUS_BADGE[e.status] || "badge-info"}`}
                  style={{ textTransform: "capitalize" }}
                >
                  {e.status}
                </span>
                {e.roll_no && (
                  <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                    Roll {e.roll_no}
                  </span>
                )}
                <span style={{ fontSize: 13, color: "var(--text-muted)", marginLeft: "auto" }}>
                  {e.enrolled_on || "—"}
                  {e.ended_on ? ` → ${e.ended_on}` : ""}
                </span>
              </div>
            ))
          )}
        </div>

        {/* Per-topic mastery (renders only when topic data exists) */}
        <TopicMasterySection studentId={id} />

        {/* Attendance breakdown */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={sectionH}>Attendance</h2>
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            <Stat label="Present" value={p.attendance.present} />
            <Stat label="Absent" value={p.attendance.absent} />
            <Stat label="Late" value={p.attendance.late} />
            <Stat label="Overall" value={p.attendance.percentage != null ? `${p.attendance.percentage}%` : "—"} />
          </div>
        </div>

        {/* Fees */}
        <div className="card" style={{ padding: 24 }}>
          <h2 style={sectionH}>Fees</h2>
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            <Stat label="Billed" value={`₹ ${Number(p.fees.total || 0).toLocaleString()}`} />
            <Stat label="Paid" value={`₹ ${Number(p.fees.paid || 0).toLocaleString()}`} />
            <Stat label="Pending" value={`₹ ${Number(p.fees.pending || 0).toLocaleString()}`} />
          </div>
        </div>

        {/* Transport (only if assigned) */}
        {p.transport && (
          <div className="card" style={{ padding: 24 }}>
            <h2 style={sectionH}>Transport</h2>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div className="stat-icon-container icon-blue"><Bus size={20} /></div>
              <div>
                <div style={{ fontWeight: 600 }}>{p.transport.route_name}</div>
                <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  {p.transport.boarding_stop ? `Stop: ${p.transport.boarding_stop}` : ""}
                  {p.transport.vehicle_number ? ` · ${p.transport.vehicle_number}` : ""}
                  {p.transport.driver_name ? ` · ${p.transport.driver_name}` : ""}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Residential (only if allocated) */}
        {p.residential && (
          <div className="card" style={{ padding: 24 }}>
            <h2 style={sectionH}>Residential</h2>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div className="stat-icon-container icon-purple"><BedDouble size={20} /></div>
              <div>
                <div style={{ fontWeight: 600 }}>{p.residential.block_name}</div>
                <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  {p.residential.room_number ? `Room ${p.residential.room_number}` : ""}
                  {p.residential.warden_name ? ` · Warden: ${p.residential.warden_name}` : ""}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <StudentLifecycleModal
        open={action !== null}
        action={action}
        studentId={id}
        studentName={p.student_name}
        currentClassId={p.class_id}
        classes={classes}
        onClose={() => setAction(null)}
        onDone={handleLifecycleDone}
      />
    </>
  );
}
