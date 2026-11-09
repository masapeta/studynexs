"use client";

import Link from "next/link";
import { Lock } from "lucide-react";
import { EmptyState } from "@/components/ui/kit";
import { NAV_GROUPS } from "@/lib/nav-groups";
import { portalHomeForRole, roleLabel } from "@/lib/permissions";

/** Name of the feature at a path, from the nav registry (longest matching prefix). */
export function featureNameForPath(pathname: string): string {
  let best = "";
  let bestLen = -1;
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      if (
        (pathname === item.href || pathname.startsWith(`${item.href}/`)) &&
        item.href.length > bestLen
      ) {
        best = item.label;
        bestLen = item.href.length;
      }
    }
  }
  return best || "this page";
}

export function AccessDenied({ pathname, role }: { pathname: string; role: string }) {
  const feature = featureNameForPath(pathname);
  return (
    <div role="alert" aria-live="polite" style={{ padding: "48px 16px" }}>
      <EmptyState
        icon={Lock}
        tone="warning"
        title={`${feature} isn't available for your role`}
        message={`Your role (${roleLabel(role)}) doesn't have access to ${feature}. If you need it, ask your school administrator.`}
        action={
          <Link href={portalHomeForRole(role)} className="btn btn-primary gw-btn-sm">
            Go to your home
          </Link>
        }
      />
    </div>
  );
}
