"use client";

import { useEffect, useState } from "react";
import { Users, UserCheck, Clock, UserX } from "lucide-react";
import { api } from "@/lib/api";

export default function AttendancePage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [selectedClass, setSelectedClass] = useState("");
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
  const [students, setStudents] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<Record<string, string>>({});
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function fetchClasses() {
      try {
        const res = await api("/api/v1/academic/classes?page_size=100");
        setClasses(res.items || res.data || []);
        if (res.items?.length > 0) setSelectedClass(res.items[0].id);
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
    async function fetchAttendanceData() {
      setLoadingData(true);
      try {
        // Fetch students in this class
        const stuRes = await api(`/api/v1/academic/students?class_id=${selectedClass}&page_size=100`);
        const stus = stuRes.items || stuRes.data || [];
        setStudents(stus);

        // Fetch existing attendance records
        const attRes = await api(`/api/v1/attendance/class/${selectedClass}?date=${selectedDate}`);
        const records = attRes.data || [];
        
        const attMap: Record<string, string> = {};
        stus.forEach((s: any) => {
          const existing = records.find((r: any) => r.student_id === s.id);
          attMap[s.id] = existing ? existing.status : "present"; // Default present
        });
        setAttendance(attMap);
      } catch (err) {
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
    try {
      const entries = Object.entries(attendance).map(([studentId, status]) => ({
        student_id: studentId,
        status,
        remarks: ""
      }));
      await api("/api/v1/attendance/mark", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClass,
          date: selectedDate,
          entries
        })
      });
      alert("Attendance saved successfully!");
    } catch (err) {
      console.error("Save attendance error", err);
      alert("Failed to save attendance.");
    } finally {
      setSaving(false);
    }
  };

  // Compute stats dynamically
  const totalStudents = students.length;
  const totalPresent = Object.values(attendance).filter(status => status === 'present').length;
  const totalAbsent = Object.values(attendance).filter(status => status === 'absent').length;
  const totalLate = Object.values(attendance).filter(status => status === 'late').length;

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Daily Attendance</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {loadingClasses ? (
            <div className="spinner" style={{ width: 20, height: 20 }} />
          ) : (
            <select 
              className="form-input" 
              value={selectedClass} 
              onChange={(e) => setSelectedClass(e.target.value)}
              style={{ width: 180, padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white" }}
            >
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.grade} - {c.section}</option>
              ))}
            </select>
          )}
          <input 
            type="date" 
            className="form-input" 
            value={selectedDate} 
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{ width: 160, padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white" }}
          />
          <button 
            className="btn btn-primary" 
            style={{ width: "auto", padding: "8px 20px", borderRadius: "var(--radius-full)" }}
            onClick={handleSave}
            disabled={loadingData || saving || students.length === 0}
          >
            {saving ? "Saving..." : "Save Attendance"}
          </button>
        </div>
      </div>

      {/* Real-time Stats */}
      <div className="bento-grid" style={{ marginBottom: 24 }}>
        <div className="card bento-col-3" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-blue"><Users size={20} /></div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>Total Students</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>{totalStudents}</div>
          </div>
        </div>
        <div className="card bento-col-3" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-green"><UserCheck size={20} /></div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>Present</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>{totalPresent}</div>
          </div>
        </div>
        <div className="card bento-col-3" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-orange"><Clock size={20} /></div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>Late</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>{totalLate}</div>
          </div>
        </div>
        <div className="card bento-col-3" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon-container icon-purple"><UserX size={20} /></div>
          <div style={{ flex: 1 }}>
            <div className="stat-label" style={{ marginBottom: 4 }}>Absent</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>{totalAbsent}</div>
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
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
              <tr><td colSpan={4} style={{ textAlign: "center", padding: 40 }}>
                <div className="spinner" style={{ margin: "0 auto" }} />
              </td></tr>
            ) : students.length === 0 ? (
              <tr><td colSpan={4} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                No students found in this class.
              </td></tr>
            ) : (
              students.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600 }}>{s.admission_number || "—"}</td>
                  <td>{s.full_name || s.user_id?.substring(0, 8)}</td>
                  <td>
                    <span className={`status-dot ${attendance[s.id] === 'present' ? 'green' : attendance[s.id] === 'absent' ? 'red' : 'orange'}`} />
                    <span style={{ textTransform: "capitalize" }}>{attendance[s.id]?.replace("_", " ") || "Present"}</span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", background: "var(--bg)", borderRadius: "var(--radius-md)", padding: 4, gap: 4 }}>
                      <button 
                        onClick={() => handleStatusChange(s.id, 'present')}
                        style={{ 
                          padding: "6px 12px", border: "none", borderRadius: "var(--radius-sm)", cursor: "pointer", fontSize: 13, fontWeight: 600,
                          background: attendance[s.id] === 'present' ? "var(--success)" : "transparent",
                          color: attendance[s.id] === 'present' ? "white" : "var(--text-secondary)",
                          transition: "0.2s"
                        }}>
                        Present
                      </button>
                      <button 
                        onClick={() => handleStatusChange(s.id, 'late')}
                        style={{ 
                          padding: "6px 12px", border: "none", borderRadius: "var(--radius-sm)", cursor: "pointer", fontSize: 13, fontWeight: 600,
                          background: attendance[s.id] === 'late' ? "var(--warning)" : "transparent",
                          color: attendance[s.id] === 'late' ? "white" : "var(--text-secondary)",
                          transition: "0.2s"
                        }}>
                        Late
                      </button>
                      <button 
                        onClick={() => handleStatusChange(s.id, 'absent')}
                        style={{ 
                          padding: "6px 12px", border: "none", borderRadius: "var(--radius-sm)", cursor: "pointer", fontSize: 13, fontWeight: 600,
                          background: attendance[s.id] === 'absent' ? "var(--danger)" : "transparent",
                          color: attendance[s.id] === 'absent' ? "white" : "var(--text-secondary)",
                          transition: "0.2s"
                        }}>
                        Absent
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
