"use client";

import type { ReactNode } from "react";
import type {
  WorkspaceBlock,
  WorkspaceVerification,
} from "@/lib/workspace-types";
import { COMPONENT_REGISTRY } from "@/lib/registry";

export function verificationLabel(verification: WorkspaceVerification): string {
  if (verification.status === "verified") return "Verified evidence";
  if (verification.status === "stale") return "Evidence may be stale";
  if (verification.status === "conflicting") return "Evidence has conflicts";
  if (verification.status === "requires_approval") return "Needs approval";
  return "Evidence missing";
}

export function MetaChip({ children }: { children: ReactNode }) {
  return (
    <span
      className="sn-filter-pill"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 10px",
        fontSize: 12,
      }}
    >
      {children}
    </span>
  );
}

export function TeacherWorkspaceBlockRenderer({
  blocks,
}: {
  blocks: WorkspaceBlock[];
}) {
  return (
    <div style={{ display: "grid", gap: 16, width: "100%" }}>
      {blocks.map((block, index) => {
        const blockType = (block as { block_type?: string }).block_type || block.type;
        const Widget = COMPONENT_REGISTRY[blockType];

        if (!Widget) {
          return (
            <div
              key={index}
              className="card"
              style={{
                margin: 0,
                padding: 16,
                border: "1px solid color-mix(in srgb, var(--danger) 40%, transparent)",
                color: "var(--danger)",
                fontSize: 14,
              }}
            >
              Unknown block: {blockType}
            </div>
          );
        }

        return <Widget key={index} {...block} />;
      })}
    </div>
  );
}

export function TeacherWorkspaceResponseMeta({
  verification,
  warnings,
  requestId,
}: {
  verification: WorkspaceVerification;
  warnings: string[];
  requestId: string;
}) {
  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap", paddingTop: 16 }}>
      {verification && <MetaChip>{verificationLabel(verification)}</MetaChip>}
      {verification?.checked_at ? <MetaChip>Checked {new Date(verification.checked_at).toLocaleString()}</MetaChip> : null}
      {warnings?.length > 0 ? <MetaChip>{warnings.length} warning{warnings.length === 1 ? "" : "s"}</MetaChip> : null}
      {requestId && <MetaChip>Request {requestId.slice(0, 8)}</MetaChip>}
    </div>
  );
}
