type Tone = "green" | "red" | "brass" | "gray" | "blue";

const TONE_CLASS: Record<Tone, string> = {
  green: "briefing-badge-green",
  red: "briefing-badge-red",
  brass: "briefing-badge-brass",
  gray: "briefing-badge-gray",
  blue: "briefing-badge-blue",
};

type Props = { tone?: Tone; children: React.ReactNode };

export function StatusBadge({ tone = "gray", children }: Props) {
  return (
    <span className={`briefing-badge ${TONE_CLASS[tone]}`}>{children}</span>
  );
}
