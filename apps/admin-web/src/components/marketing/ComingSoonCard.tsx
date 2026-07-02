"use client";

import Link from "next/link";
import { ArrowRight, Clock } from "lucide-react";
import { FadeIn } from "./Motion";

type Props = {
  name: string;
  tagline: string;
  status: string;
  href?: string;
  delay?: number;
};

export function ComingSoonCard({ name, tagline, status, href, delay = 0 }: Props) {
  const inner = (
  <>
      <div className="mkt-coming-soon-badge">
        <Clock size={12} aria-hidden />
        {status}
      </div>
      <h3 className="mkt-h3">{name}</h3>
      <p className="mkt-coming-soon-tagline">{tagline}</p>
      {href && (
        <span className="mkt-coming-soon-link">
          Learn more <ArrowRight size={14} aria-hidden />
        </span>
      )}
    </>
  );

  return (
    <FadeIn delay={delay} className="mkt-coming-soon-card mkt-glass">
      {href ? (
        <Link href={href} className="mkt-coming-soon-inner">
          {inner}
        </Link>
      ) : (
        <div className="mkt-coming-soon-inner">{inner}</div>
      )}
    </FadeIn>
  );
}

export function FeatureChipGrid({ items }: { items: readonly string[] }) {
  return (
    <ul className="mkt-feature-chips">
      {items.map((item, i) => (
        <li key={item} className="mkt-feature-chip mkt-glass" style={{ animationDelay: `${i * 0.02}s` }}>
          {item}
        </li>
      ))}
    </ul>
  );
}
