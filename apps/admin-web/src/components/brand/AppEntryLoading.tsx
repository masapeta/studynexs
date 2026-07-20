"use client";

import { motion, useReducedMotion } from "framer-motion";
import { PlatformMark } from "./PlatformMark";
import {
  PLATFORM_PRODUCT_NAME,
  entryMessageForPortal,
  type PortalEntryContext,
} from "@/lib/platform-brand";
import { PLATFORM_MOTION } from "@/lib/platform-motion";

type Props = {
  /** Portal context — preferred API for all authenticated shells. */
  portal?: PortalEntryContext;
  /** @deprecated Use `portal` instead. */
  contextLabel?: string;
};

/**
 * Branded entry loading — single shared component for every portal shell.
 * Emotional bridge from marketing/login into the app (Phase 0 / 0.5).
 */
export function AppEntryLoading({ portal = "default", contextLabel }: Props) {
  const reduce = useReducedMotion();
  const message = contextLabel
    ? `Opening ${contextLabel}…`
    : entryMessageForPortal(portal);

  const fade = reduce
    ? {}
    : {
        initial: { opacity: 0, y: 8 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: PLATFORM_MOTION.durationEnter, ease: PLATFORM_MOTION.ease },
      };

  return (
    <div className="sn-app sn-entry-loading" role="status" aria-live="polite" aria-busy="true">
      <div className="sn-app-bg" aria-hidden>
        <div className="sn-app-mesh" />
        <div className="sn-app-grid" />
        <div className="sn-app-orb sn-app-orb--1" />
        <div className="sn-app-orb sn-app-orb--2" />
      </div>

      <motion.div className="sn-entry-loading-inner" {...fade}>
        <div className="sn-entry-loading-brand">
          <PlatformMark variant="studynexs" size="lg" />
          <div className="sn-entry-loading-copy">
            <span className="platform-text-entry-product">{PLATFORM_PRODUCT_NAME}</span>
            <span className="platform-text-entry-message">{message}</span>
          </div>
        </div>

        <div className="sn-entry-loading-preview" aria-hidden>
          <div className="sn-entry-loading-preview-row">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="sn-entry-shimmer sn-entry-shimmer--kpi" />
            ))}
          </div>
          <div className="sn-entry-loading-preview-row sn-entry-loading-preview-row--panels">
            {[0, 1, 2].map((i) => (
              <div key={i} className="sn-entry-shimmer sn-entry-shimmer--panel" />
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/** Canonical export for portal layouts — use this in every shell. */
export function PortalEntryLoading(props: Props) {
  return <AppEntryLoading {...props} />;
}
