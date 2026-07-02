"use client";

import Link from "next/link";
import { ArrowRight, GraduationCap, Layers } from "lucide-react";
import { FadeIn } from "./Motion";

type Props = {
  name: string;
  tagline: string;
  description: string;
  href: string;
  category: string;
  accent: "education" | "enterprise";
  delay?: number;
};

const ICONS = {
  education: GraduationCap,
  enterprise: Layers,
};

export function ProductHubCard({
  name,
  tagline,
  description,
  href,
  category,
  accent,
  delay = 0,
}: Props) {
  const Icon = ICONS[accent];

  return (
    <FadeIn delay={delay}>
      <Link href={href} className={`mkt-product-hub-card mkt-glass mkt-product-hub-card--${accent}`}>
        <div className="mkt-product-hub-card-glow" aria-hidden />
        <div className="mkt-product-hub-card-top">
          <span className="mkt-product-hub-card-icon">
            <Icon size={20} strokeWidth={1.75} aria-hidden />
          </span>
          <span className="mkt-product-hub-card-category">{category}</span>
        </div>
        <h2 className="mkt-h3">{name}</h2>
        <p className="mkt-product-hub-tagline">{tagline}</p>
        <p className="mkt-product-hub-desc">{description}</p>
        <span className="mkt-product-hub-cta">
          View product <ArrowRight size={16} aria-hidden />
        </span>
      </Link>
    </FadeIn>
  );
}
