"use client";

import type { ElementType } from "react";
import {
  Home,
  MessageSquarePlus,
  GraduationCap,
  ListChecks,
  History,
  Settings,
  LayoutGrid,
} from "lucide-react";

export type SlimNavKey =
  | "home"
  | "new-chat"
  | "academics"
  | "tasks"
  | "history"
  | "settings"
  | "modules";

interface SlimItem {
  key: SlimNavKey;
  label: string;
  icon: ElementType;
}

const ITEMS: SlimItem[] = [
  { key: "home", label: "Home", icon: Home },
  { key: "new-chat", label: "New chat", icon: MessageSquarePlus },
  { key: "academics", label: "My academics", icon: GraduationCap },
  { key: "tasks", label: "Tasks & requests", icon: ListChecks },
  { key: "history", label: "History", icon: History },
];

export function WorkspaceSlimNav({
  active,
  brand,
  onSelect,
  onOpenModules,
  onOpenSettings,
}: {
  active: SlimNavKey;
  brand: string;
  onSelect: (key: SlimNavKey) => void;
  onOpenModules: () => void;
  onOpenSettings: () => void;
}) {
  return (
    <nav className="sn-ws-slim" aria-label="Workspace navigation">
      <div className="sn-ws-slim__brand" title={brand} aria-hidden>
        {brand.trim().charAt(0).toUpperCase() || "S"}
      </div>

      {ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.key}
            type="button"
            className={`sn-ws-slim__btn${active === item.key ? " sn-ws-slim__btn--active" : ""}`}
            title={item.label}
            aria-label={item.label}
            aria-current={active === item.key ? "page" : undefined}
            onClick={() => onSelect(item.key)}
          >
            <Icon size={20} strokeWidth={1.9} />
          </button>
        );
      })}

      <button
        type="button"
        className="sn-ws-slim__btn"
        title="All modules"
        aria-label="All modules"
        onClick={onOpenModules}
      >
        <LayoutGrid size={20} strokeWidth={1.9} />
      </button>

      <div className="sn-ws-slim__spacer" />

      <button
        type="button"
        className="sn-ws-slim__btn"
        title="Settings"
        aria-label="Settings"
        onClick={onOpenSettings}
      >
        <Settings size={20} strokeWidth={1.9} />
      </button>
    </nav>
  );
}
