import type { HTMLAttributes } from "react";
import { PLATFORM_MARKS, type PlatformMarkVariant } from "@/lib/platform-brand";

export type PlatformMarkSize = "sm" | "md" | "lg";

type Props = HTMLAttributes<HTMLSpanElement> & {
  variant?: PlatformMarkVariant;
  size?: PlatformMarkSize;
  /** Override letter (rare — prefer variant). */
  letter?: string;
};

/**
 * Shared platform letter mark — one component for marketing nav and app chrome.
 * Styles: platform-tokens.css + platform-typography.css
 */
export function PlatformMark({
  variant = "studynexs",
  size = "md",
  letter,
  className = "",
  ...rest
}: Props) {
  const glyph = letter ?? PLATFORM_MARKS[variant];
  return (
    <span
      className={`platform-mark platform-mark--${size}${className ? ` ${className}` : ""}`}
      aria-hidden
      {...rest}
    >
      {glyph}
    </span>
  );
}
