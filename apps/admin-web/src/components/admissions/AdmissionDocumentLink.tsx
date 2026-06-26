"use client";

import { useState } from "react";
import { fetchProtectedDocumentUrl } from "@/lib/api";

type Props = {
  fileId: string;
  fileName?: string | null;
};

export function AdmissionDocumentLink({ fileId, fileName }: Props) {
  const [loading, setLoading] = useState(false);

  async function openDoc() {
    setLoading(true);
    try {
      const url = await fetchProtectedDocumentUrl(`/api/v1/files/${fileId}`);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      window.alert("Could not open document.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      className="gw-doc-link"
      onClick={openDoc}
      disabled={loading}
    >
      {loading ? "Opening…" : fileName || "View document"}
    </button>
  );
}
