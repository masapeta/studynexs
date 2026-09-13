"use client";

import { ArrowRight } from "lucide-react";
import type { WorkspaceActionDef } from "@/lib/workspace-actions";

export function ActionWidgetGrid({
  actions,
  onRun,
}: {
  actions: WorkspaceActionDef[];
  onRun: (action: WorkspaceActionDef) => void;
}) {
  return (
    <div className="sn-ws-actions">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <button
            key={action.id}
            type="button"
            className="sn-ws-action"
            onClick={() => onRun(action)}
            aria-label={action.label}
          >
            <div className="sn-ws-action__top">
              <span className="sn-ws-action__icon">
                <Icon size={20} strokeWidth={1.9} />
              </span>
              <ArrowRight size={16} style={{ color: "var(--text-muted)" }} aria-hidden />
            </div>
            <div>
              <div className="sn-ws-action__label">{action.label}</div>
              <div className="sn-ws-action__desc">{action.description}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
