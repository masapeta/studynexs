"use client";

import Link from "next/link";
import type { ElementType } from "react";
import { X } from "lucide-react";
import { NAV_GROUPS, DEFAULT_OFF_MODULES, type NavItem } from "@/lib/nav-groups";
import { navAllowed, type UserPermissions } from "@/lib/permissions";

export interface DrawerGroup {
  label: string;
  items: Array<{ href: string; label: string; icon?: ElementType }>;
}

export function WorkspaceModulesDrawer({
  open,
  permissions,
  modules,
  groups,
  onClose,
}: {
  open: boolean;
  permissions: UserPermissions | null;
  modules: Record<string, boolean>;
  /** Custom nav groups (parent/student). When omitted, uses staff NAV_GROUPS. */
  groups?: DrawerGroup[];
  onClose: () => void;
}) {
  if (!open) return null;

  const moduleVisible = (m?: string) => {
    if (!m) return true;
    if (DEFAULT_OFF_MODULES.has(m)) return modules[m] === true;
    return modules[m] !== false;
  };

  const itemVisible = (item: NavItem) => {
    if (item.roles && permissions && !item.roles.includes(permissions.role)) return false;
    if (item.roles && !item.perm && !item.anyPerm) return true;
    if (item.anyPerm && permissions) {
      if (!item.anyPerm.some((p) => permissions[p])) return false;
    } else if (item.perm && permissions && !permissions[item.perm]) {
      return false;
    }
    return navAllowed(item.href, permissions);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="All modules"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 80,
        display: "flex",
      }}
    >
      <div
        onClick={onClose}
        aria-hidden
        style={{ position: "absolute", inset: 0, background: "rgba(15,23,42,0.35)" }}
      />
      <div
        style={{
          position: "relative",
          marginLeft: "auto",
          width: "min(420px, 92vw)",
          height: "100%",
          background: "var(--bg-card)",
          borderLeft: "1px solid var(--border)",
          boxShadow: "-12px 0 40px rgba(15,23,42,0.16)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 18px",
            borderBottom: "1px solid var(--border)",
          }}
        >
          <strong style={{ fontSize: 15, color: "var(--text-primary)" }}>All modules</strong>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modules"
            className="sn-ws-panel__close"
          >
            <X size={16} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: 18, display: "grid", gap: 20 }}>
          {groups
            ? groups.map((group) => (
                <div key={group.label}>
                  <div className="sn-ws-panel__section-label">{group.label}</div>
                  <div style={{ display: "grid", gap: 8 }}>
                    {group.items.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={onClose}
                          className="card"
                          style={{
                            margin: 0,
                            padding: "12px 14px",
                            display: "flex",
                            alignItems: "center",
                            gap: 12,
                            textDecoration: "none",
                            color: "var(--text-primary)",
                          }}
                        >
                          <span
                            style={{
                              display: "inline-flex",
                              width: 34,
                              height: 34,
                              borderRadius: 10,
                              alignItems: "center",
                              justifyContent: "center",
                              background: "var(--accent-50)",
                              color: "var(--accent-dark)",
                            }}
                          >
                            {Icon ? <Icon size={17} strokeWidth={1.9} /> : null}
                          </span>
                          <span style={{ fontSize: 14, fontWeight: 600 }}>{item.label}</span>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))
            : NAV_GROUPS.map((group) => {
                const items = group.items.filter(
                  (item) => moduleVisible(item.module) && itemVisible(item)
                );
                if (!items.length) return null;
                return (
              <div key={group.label}>
                <div className="sn-ws-panel__section-label">{group.label}</div>
                <div style={{ display: "grid", gap: 8 }}>
                  {items.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={onClose}
                        className="card"
                        style={{
                          margin: 0,
                          padding: "12px 14px",
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          textDecoration: "none",
                          color: "var(--text-primary)",
                        }}
                      >
                        <span
                          style={{
                            display: "inline-flex",
                            width: 34,
                            height: 34,
                            borderRadius: 10,
                            alignItems: "center",
                            justifyContent: "center",
                            background: "var(--accent-50)",
                            color: "var(--accent-dark)",
                          }}
                        >
                          <Icon size={17} strokeWidth={1.9} />
                        </span>
                        <span style={{ fontSize: 14, fontWeight: 600 }}>{item.label}</span>
                      </Link>
                    );
                  })}
                </div>
              </div>
                );
              })}
        </div>
      </div>
    </div>
  );
}
