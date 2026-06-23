"use client";

import { useEffect, useRef } from "react";
import { Printer, X } from "lucide-react";

type Props = {
  title: string;
  blobUrl: string;
  onClose: () => void;
};

/** In-app print preview — no new browser tabs or popups. */
export function DocumentPreviewModal({ title, blobUrl, onClose }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function printDoc() {
    try {
      iframeRef.current?.contentWindow?.print();
    } catch {
      /* cross-origin edge case — user can still use browser print on the iframe */
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(15, 23, 42, 0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{
          width: "min(920px, 100%)",
          height: "min(90vh, 900px)",
          display: "flex",
          flexDirection: "column",
          padding: 0,
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            padding: "12px 16px",
            borderBottom: "1px solid var(--border)",
            background: "var(--bg)",
          }}
        >
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{title}</h2>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className="btn btn-primary" onClick={printDoc} style={{ width: "auto", padding: "8px 16px" }}>
              <Printer size={15} /> Print
            </button>
            <button type="button" className="btn btn-outline" onClick={onClose} style={{ width: "auto", padding: "8px 12px" }}>
              <X size={15} /> Close
            </button>
          </div>
        </div>
        <iframe
          ref={iframeRef}
          src={blobUrl}
          title={title}
          style={{ flex: 1, width: "100%", border: "none", background: "white" }}
        />
      </div>
    </div>
  );
}
