/** Skip link — first focusable element for keyboard users (WCAG 2.4.1). */
export function SkipLink({
  targetId = "main-content",
  label = "Skip to main content",
}: {
  targetId?: string;
  label?: string;
}) {
  return (
    <a href={`#${targetId}`} className="platform-skip-link">
      {label}
    </a>
  );
}
