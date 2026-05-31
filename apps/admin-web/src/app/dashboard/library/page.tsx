"use client";
export default function LibraryPage() {
  return (
    <>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Library</h1>
      <div className="card" style={{ padding: 40, textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>📚</div>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Library Management</h2>
        <p style={{ color: "var(--text-muted)", maxWidth: 400, margin: "0 auto" }}>
          Manage books, track issues, and monitor returns.
        </p>
      </div>
    </>
  );
}
