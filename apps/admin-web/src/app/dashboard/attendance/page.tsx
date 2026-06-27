"use client";

import { useEffect, useMemo, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { FilterPillBar } from "@/components/layout/FilterPillBar";
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

  const selectedClassLabel = useMemo(() => {
    const match = classes.find((c) => c.id === selectedClass);
    return match ? formatClassLabel(match.grade, match.section) : "";
  }, [classes, selectedClass]);

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
    <>
      <PageHeaderCard title="Attendance" subtitle="Mark and review class attendance for the selected date.">
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
          className="btn btn-primary sn-filter-pill"
          onClick={handleSave}
          disabled={loadingData || saving || students.length === 0}
        >
          {saving ? "Saving…" : "Save Attendance"}
        </button>
      </PageHeaderCard>

      {error && (
        <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>
          {error}
        </div>
      )}

      <FilterPillBar
        tabs={FILTER_TILES.map(({ key, label }) => ({
          key,
          label,
          count: counts[key],
        }))}
        activeKey={statusFilter}
        onChange={(key) => toggleStatusFilter(key as AttendanceFilter)}
        ariaLabel="Filter by attendance status"
      />

      <div className="data-table-card">
        <table className="attendance-table" aria-label="Class attendance">
          <colgroup>
            <col className="attendance-col-adm" />
            <col className="attendance-col-name" />
            <col className="attendance-col-status" />
            <col className="attendance-col-mark" />
          </colgroup>
          <thead>
            <tr>
              <th>Admission No.</th>
              <th>Student Name</th>
              <th>Current Status</th>
              <th>Mark Attendance</th>
            </tr>
          </thead>
          <tbody>
            {loadingData ? (
              <tr>
                <td colSpan={4} className="attendance-table-empty">
                  <div className="spinner" style={{ margin: "0 auto" }} />
                </td>
              </tr>
            ) : students.length === 0 ? (
              <tr>
                <td colSpan={4} className="attendance-table-empty">
                  No students found in this class.
                </td>
              </tr>
            ) : filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={4} className="attendance-table-empty">
                  {emptyFilterMessage}
                </td>
              </tr>
            ) : (
              filteredStudents.map((s) => {
                const status = attendance[s.id] || "present";
                return (
                  <tr key={s.id} className="attendance-table-row">
                    <td className="attendance-table-adm">{s.admission_no || "—"}</td>
                    <td className="attendance-table-name">{s.student_name || "—"}</td>
                    <td>
                      <StatusBadge tone={STATUS_TONE[status as keyof typeof STATUS_TONE] || "gray"}>
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                      </StatusBadge>
                    </td>
                    <td className="attendance-table-mark">
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

        {students.length > 0 && !loadingData && (
          <div className="data-table-footer">
            <span>
              {statusFilter === "all"
                ? `${filteredStudents.length} student${filteredStudents.length === 1 ? "" : "s"}`
                : `Showing ${filteredStudents.length} of ${students.length} students`}
            </span>
            <span>
              {selectedClassLabel}
              {selectedClassLabel ? " · " : ""}
              {selectedDate}
            </span>
          </div>
        )}
      </div>
    </>
  );
}
