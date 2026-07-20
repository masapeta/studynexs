"use client";

import { PlatformMark } from "./PlatformMark";
import { PLATFORM_PRODUCT_NAME } from "@/lib/platform-brand";

type Props = {
  /** Full school name shown under the StudyNexs product line. */
  schoolName?: string;
  /** Compact variant for tight spaces (sidebar default). */
  compact?: boolean;
};

/**
 * Platform + school brand hierarchy for app chrome.
 * StudyNexs product identity is always primary; school name coexists below.
 */
export function StudyNexsBrandMark({ schoolName, compact = false }: Props) {
  return (
    <div className="sidebar-brand">
      <PlatformMark variant="studynexs" size="md" className="sidebar-brand-mark" />
      <div className="sidebar-brand-text">
        <span className="sidebar-brand-line platform-text-product">{PLATFORM_PRODUCT_NAME}</span>
        {schoolName ? (
          <span
            className={`sidebar-brand-line platform-text-school${compact ? " sidebar-brand-line--school" : ""}`}
          >
            {schoolName}
          </span>
        ) : null}
      </div>
    </div>
  );
}
