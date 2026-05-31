"use client";
export default function TimetablePage() {
  return (
    <>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Timetable</h1>
      <div className="card" style={{ padding: 40, textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>📅</div>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Class Schedules</h2>
        <p style={{ color: "var(--text-muted)", maxWidth: 400, margin: "0 auto" }}>
          Manage timetable slots, assign teachers, and view weekly schedules.
        </p>
      </div>
    </>
  );
}
