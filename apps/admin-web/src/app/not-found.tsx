import Link from "next/link";

export default function NotFound() {
  return (
    <div
      style={{
        minHeight: "70vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "1rem",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "3rem", fontWeight: 800, letterSpacing: "-0.03em", margin: 0 }}>
        404
      </div>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>Page not found</h1>
      <p style={{ color: "#64748b", fontSize: "0.95rem", maxWidth: 380, margin: 0 }}>
        The page you&apos;re looking for doesn&apos;t exist or may have moved.
      </p>
      <Link
        href="/"
        style={{
          padding: "0.6rem 1.2rem",
          borderRadius: 10,
          border: "none",
          background: "#2563eb",
          color: "#fff",
          fontWeight: 600,
          textDecoration: "none",
        }}
      >
        Back to home
      </Link>
    </div>
  );
}
