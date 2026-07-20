/**
 * Motion constants mirroring platform-tokens.css — keep in sync for JS animation APIs.
 * Phase 3A: framer-motion and exit timeouts consume these values.
 */
export const PLATFORM_MOTION = {
  ease: [0.22, 1, 0.36, 1] as const,
  durationEnter: 0.55,
  durationFast: 0.35,
  durationMedium: 0.25,
} as const;

/** Milliseconds for modal exit unmount delay (matches --platform-duration-fast). */
export const PLATFORM_MOTION_MS = {
  fast: Math.round(PLATFORM_MOTION.durationFast * 1000),
  enter: Math.round(PLATFORM_MOTION.durationEnter * 1000),
} as const;
