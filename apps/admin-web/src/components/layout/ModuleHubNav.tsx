"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type ModuleHubTab = {
  href: string;
  label: string;
  /** Custom active check (e.g. enrolled students incl. profile, excl. other tabs). */
  isActive?: (pathname: string) => boolean;
  /** Match nested routes (default true). Set false for exact-only. */
  matchNested?: boolean;
};

type Props = {
  tabs: ModuleHubTab[];
  ariaLabel: string;
};

function isTabActive(pathname: string, tab: ModuleHubTab): boolean {
  if (tab.isActive) return tab.isActive(pathname);
  if (tab.matchNested === false) {
    return pathname === tab.href;
  }
  return pathname === tab.href || pathname.startsWith(`${tab.href}/`);
}

export function ModuleHubNav({ tabs, ariaLabel }: Props) {
  const pathname = usePathname();

  return (
    <nav className="sn-module-hub-nav" aria-label={ariaLabel}>
      {tabs.map((tab) => {
        const active = isTabActive(pathname, tab);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`sn-module-hub-tab${active ? " sn-module-hub-tab--active" : ""}`}
            aria-current={active ? "page" : undefined}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
