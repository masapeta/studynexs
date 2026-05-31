"use client";
export default function SettingsPage() {
  return (
    <>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>Settings</h1>
      <div className="card" style={{ padding: 40, textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>⚙️</div>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>School Settings</h2>
        <p style={{ color: "var(--text-muted)", maxWidth: 400, margin: "0 auto" }}>
          Configure school profile, academic years, fee structures, and system preferences.
        </p>
      </div>
    </>
  );
}
