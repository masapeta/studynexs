"use client";

import { useEffect, useMemo, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { AppSelect } from "@/components/ui/AppSelect";
import { formatClassLabel, sortClasses } from "@/lib/format";

type AttendanceFilter = "all" | "present" | "late" | "absent";

const FILTER_TILES: { key: AttendanceFilter; label: string }[] = [
  { key: "all", label: "Total Students" },
  { key: "present", label: "Present" },
  { key: "late", label: "Late" },
  { key: "absent", label: "Absent" },
];

const STATUS_TONE = {
  present: "green",
  late: "brass",
  absent: "red",
} as const;

export default function AttendancePage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [selectedClass, setSelectedClass] = useState("");
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
  const [students, setStudents] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<Record<string, string>>({});
  const [statusFilter, setStatusFilter] = useState<AttendanceFilter>("all");
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchClasses() {
      try {
        const res = await api("/api/v1/academic/classes?page_size=100");
        const list = sortClasses<any>(res.items || res.data || []);
        setClasses(list);
        if (list.length > 0) setSelectedClass(list[0].id);
      } catch (err) {
        console.error("Fetch classes error", err);
      } finally {
        setLoadingClasses(false);
      }
    }
    fetchClasses();
  }, []);

  useEffect(() => {
    if (!selectedClass || !selectedDate) return;
    setStatusFilter("all");
    async function fetchAttendanceData() {
      setLoadingData(true);
      setError("");
      try {
        const stuRes = await api(`/api/v1/academic/students?class_id=${selectedClass}&page_size=100`);
        const stus = stuRes.items || stuRes.data || [];
        setStudents(stus);

        const attRes = await api(`/api/v1/attendance/class/${selectedClass}?date=${selectedDate}`);
        const records = attRes.data || [];

        const attMap: Record<string, string> = {};
        stus.forEach((s: any) => {
          const existing = records.find((r: any) => r.student_id === s.id);
          attMap[s.id] = existing ? existing.status : "present";
        });
        setAttendance(attMap);
      } catch (err) {
        setError(getApiErrorMessage(err, "Failed to load attendance"));
        console.error("Fetch attendance data error", err);
      } finally {
        setLoadingData(false);
      }
    }
    fetchAttendanceData();
  }, [selectedClass, selectedDate]);

  const handleStatusChange = (studentId: string, status: string) => {
    setAttendance((prev) => ({ ...prev, [studentId]: status }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const entries = Object.entries(attendance).map(([studentId, status]) => ({
        student_id: studentId,
        status,
        remarks: "",
      }));
      await api("/api/v1/attendance/mark", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClass,
          date: selectedDate,
          entries,
        }),
      });
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to save attendance"));
      console.error("Save attendance error", err);
    } finally {
      setSaving(false);
    }
  };

  const counts: Record<AttendanceFilter, number> = {
    all: students.length,
    present: Object.values(attendance).filter((s) => s === "present").length,
    late: Object.values(attendance).filter((s) => s === "late").length,
    absent: Object.values(attendance).filter((s) => s === "absent").length,
  };

  const filteredStudents = useMemo(() => {
    if (statusFilter === "all") return students;
    return students.filter((s) => attendance[s.id] === statusFilter);
  }, [students, attendance, statusFilter]);

  function toggleStatusFilter(filter: AttendanceFilter) {
    if (filter === "all") {
      setStatusFilter("all");
      return;
    }
    setStatusFilter((current) => (current === filter ? "all" : filter));
  }

  const emptyFilterMessage = (() => {
    if (statusFilter === "all") return "No students found in this class.";
    const label = FILTER_TILES.find((t) => t.key === statusFilter)?.label.toLowerCase() ?? statusFilter;
    return `No ${label} for this class on the selected date.`;
  })();

  return (
    <PageShell
      title="Daily Attendance"
      subtitle="Mark and review class attendance for the selected date."
      action={
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          {loadingClasses ? (
            <div className="spinner" style={{ width: 20, height: 20 }} />
          ) : (
            <AppSelect
              variant="pill"
              value={selectedClass}
              onChange={setSelectedClass}
              aria-label="Select class"
              style={{ width: 180 }}
              options={classes.map((c) => ({
                value: c.id,
                label: formatClassLabel(c.grade, c.section),
              }))}
            />
          )}
          <input
            type="date"
            className="form-input"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            aria-label="Attendance date"
            style={{ width: 160 }}
          />
          <button
            type="button"
            className="btn btn-primary gw-btn-sm"
            onClick={handleSave}
            disabled={loadingData || saving || students.length === 0}
          >
            {saving ? "Saving…" : "Save Attendance"}
          </button>
        </div>
      }
    >
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="gw-pipeline" role="tablist" aria-label="Filter by attendance status">
        {FILTER_TILES.map(({ key, label }) => {
          const active = statusFilter === key;
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={active}
              className={`gw-pipeline-stage${active ? " gw-pipeline-stage-active" : ""}`}
              onClick={() => toggleStatusFilter(key)}
            >
              <span className="gw-pipeline-count">{counts[key]}</span>
              <span className="gw-pipeline-label">{label}</span>
            </button>
          );
        })}
      </div>

      <div className="data-table-card">
        <table className="data-table" aria-label="Class attendance">
          <thead>
            <tr>
              <th>Student ID</th>
              <th>Student Name</th>
              <th>Current Status</th>
              <th style={{ textAlign: "right" }}>Mark Attendance</th>
            </tr>
          </thead>
          <tbody>
            {loadingData ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", padding: 40 }}>
                  <div className="spinner" style={{ margin: "0 auto" }} />
                </td>
              </tr>
            ) : students.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                  No students found in this class.
                </td>
              </tr>
            ) : filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                  {emptyFilterMessage}
                </td>
              </tr>
            ) : (
              filteredStudents.map((s) => {
                const status = attendance[s.id] || "present";
                return (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.admission_no || "—"}</td>
                    <td>{s.student_name || "—"}</td>
                    <td>
                      <StatusBadge tone={STATUS_TONE[status as keyof typeof STATUS_TONE] || "gray"}>
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                      </StatusBadge>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div className="gw-attendance-mark">
                        {(["present", "late", "absent"] as const).map((value) => (
                          <button
                            key={value}
                            type="button"
                            className={`gw-attendance-mark-btn gw-attendance-mark-btn--${value}${
                              status === value ? " gw-attendance-mark-btn--active" : ""
                            }`}
                            onClick={() => handleStatusChange(s.id, value)}
                          >
                            {value.charAt(0).toUpperCase() + value.slice(1)}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </PageShell>
  );
}
