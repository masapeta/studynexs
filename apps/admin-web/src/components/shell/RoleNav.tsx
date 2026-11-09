"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ElementType } from "react";
import {
  History,
  Home,
  Menu,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  School,
  Settings,
  X,
} from "lucide-react";
import type { NavGroup } from "@/lib/nav-groups";

export type ShellNavItem = { href: string; label: string; icon?: ElementType };

/**
 * Persona nav. Every entry is a link or a real action — no decorative controls.
 * Collapses to an icon rail (persisted) on desktop; becomes a bottom bar on phones.
 */
export function RoleNav({
  brand,
  homeHref,
  chatHref,
  groups,
  myClassesHref,
  settingsHref,
  collapsed,
  onToggleCollapsed,
  onNewChat,
  onOpenHistory,
}: {
  brand: string;
  homeHref: string;
  chatHref: string;
  groups: NavGroup[] | { label: string; items: ShellNavItem[] }[];
  myClassesHref?: string;
  settingsHref?: string;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onNewChat: () => void;
  onOpenHistory: () => void;
}) {
  const pathname = usePathname();
  // Phones: the bottom bar shows primary items; "Menu" opens every section as a sheet.
  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetPath, setSheetPath] = useState(pathname);
  if (sheetPath !== pathname) {
    setSheetPath(pathname);
    setSheetOpen(false);
  }
  const isActive = (href: string) =>
    href === homeHref ? pathname === homeHref : pathname === href || pathname.startsWith(`${href}/`);

  const link = (href: string, label: string, Icon: ElementType | undefined, primary = false) => (
    <Link
      key={href + label}
      href={href}
      className={`sn-rnav__item${isActive(href) ? " sn-rnav__item--active" : ""}${primary ? " sn-rnav__item--primary" : ""}`}
      aria-current={isActive(href) ? "page" : undefined}
      title={collapsed ? label : undefined}
    >
      {Icon ? <Icon size={18} strokeWidth={1.9} aria-hidden /> : <span className="sn-rnav__dot" aria-hidden />}
      <span className="sn-rnav__label">{label}</span>
    </Link>
  );

  return (
    <nav
      className={`sn-rnav${collapsed ? " sn-rnav--collapsed" : ""}${sheetOpen ? " sn-rnav--sheet-open" : ""}`}
      aria-label="Main navigation"
    >
      <div className="sn-rnav__head">
        <span className="sn-rnav__brand" aria-hidden>{brand.trim().charAt(0).toUpperCase() || "S"}</span>
        <span className="sn-rnav__brand-name">{brand || "StudyNexs"}</span>
        <button
          type="button"
          className="sn-rnav__collapse"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          aria-expanded={!collapsed}
        >
          {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      <div className="sn-rnav__scroll">
        <div className="sn-rnav__group">
          {link(homeHref, "Home", Home, true)}
          {myClassesHref ? link(myClassesHref, "My classes", School, true) : null}
          <Link href={chatHref} className="sn-rnav__item sn-rnav__item--primary" onClick={onNewChat}
                title={collapsed ? "New chat" : undefined}>
            <MessageSquarePlus size={18} strokeWidth={1.9} aria-hidden />
            <span className="sn-rnav__label">New chat</span>
          </Link>
          <button type="button" className="sn-rnav__item sn-rnav__item--primary" onClick={onOpenHistory}
                  title={collapsed ? "Conversations" : undefined}>
            <History size={18} strokeWidth={1.9} aria-hidden />
            <span className="sn-rnav__label">Conversations</span>
          </button>
          <button
            type="button"
            className="sn-rnav__item sn-rnav__item--primary sn-rnav__menu"
            onClick={() => setSheetOpen((o) => !o)}
            aria-expanded={sheetOpen}
            aria-label={sheetOpen ? "Close menu" : "Open menu"}
          >
            {sheetOpen ? <X size={18} aria-hidden /> : <Menu size={18} strokeWidth={1.9} aria-hidden />}
            <span className="sn-rnav__label">{sheetOpen ? "Close" : "Menu"}</span>
          </button>
        </div>

        {groups.map((g) => {
          const items = g.items.filter((i) => i.href !== homeHref);
          if (items.length === 0) return null;
          return (
            <div key={g.label} className="sn-rnav__group sn-rnav__group--secondary">
              <div className="sn-rnav__group-label">{g.label}</div>
              {items.map((i) => link(i.href, i.label, i.icon))}
            </div>
          );
        })}
      </div>

      {settingsHref ? (
        <div className="sn-rnav__foot sn-rnav__group--secondary">{link(settingsHref, "Settings", Settings)}</div>
      ) : null}
    </nav>
  );
}
