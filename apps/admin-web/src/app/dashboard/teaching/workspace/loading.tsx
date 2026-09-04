export default function Loading() {
  return (
    <div className="gw-page sn-page-shell" role="status" aria-label="Loading Teacher Copilot">
      <div className="sn-workspace sn-workspace--primary" style={{ padding: 20, marginBottom: 16 }}>
        <div className="sn-workspace-zone" style={{ display: "grid", gap: 12 }}>
          <div className="skeleton" style={{ height: 28, width: 220, borderRadius: 12 }} />
          <div className="skeleton" style={{ height: 72, width: "100%", borderRadius: 16 }} />
          <div className="skeleton" style={{ height: 40, width: 180, borderRadius: 999 }} />
        </div>
      </div>
      <div className="sn-workspace sn-workspace--secondary" style={{ padding: 20 }}>
        <div className="sn-workspace-zone" style={{ display: "grid", gap: 12 }}>
          <div className="skeleton" style={{ height: 22, width: 280, borderRadius: 12 }} />
          <div className="skeleton" style={{ height: 120, width: "100%", borderRadius: 16 }} />
        </div>
      </div>
    </div>
  );
}