"use client";

import Link from "next/link";
import { Building2, Sparkles } from "lucide-react";
import { NOUSTRIKS } from "@/lib/noustriks-content";
import { FadeIn } from "./Motion";

export function BuiltByNoustriks() {
  return (
    <p className="mkt-built-by">
      Proudly built by{" "}
      <Link href="/company" className="mkt-built-by-link">
        Noustriks
      </Link>
      <span className="mkt-built-by-sep" aria-hidden>
        ·
      </span>
      <Link href="/products" className="mkt-built-by-link mkt-built-by-link--muted">
        View products
      </Link>
    </p>
  );
}

export function AboutNoustriksSection() {
  return (
    <section
      className="mkt-section mkt-section--noustriks"
      id="noustriks"
      aria-labelledby="noustriks-heading"
    >
      <div className="mkt-container">
        <FadeIn>
          <div className="mkt-noustriks-panel mkt-glass-strong">
            <div className="mkt-noustriks-panel-glow" aria-hidden />
            <div className="mkt-noustriks-panel-grid">
              <div className="mkt-noustriks-panel-copy">
                <div className="mkt-eyebrow mkt-glass mkt-eyebrow--inline">
                  <Building2 size={12} aria-hidden />
                  About Noustriks
                </div>
                <h2 id="noustriks-heading" className="mkt-h2 mkt-h2--section">
                  {NOUSTRIKS.aboutTitle}
                </h2>
                <p className="mkt-lead mkt-lead--section">{NOUSTRIKS.description}</p>
                <p className="mkt-noustriks-body">{NOUSTRIKS.mission}</p>
                <div className="mkt-noustriks-actions">
                  <Link href="/company" className="mkt-btn mkt-btn--glass">
                    Company overview
                  </Link>
                  <Link href="/products" className="mkt-btn mkt-btn--ghost">
                    Explore products →
                  </Link>
                </div>
              </div>
              <div className="mkt-noustriks-tree mkt-glass" aria-label="Noustriks product hierarchy">
                <div className="mkt-noustriks-tree-root">
                  <span className="mkt-noustriks-tree-mark" aria-hidden>
                    N
                  </span>
                  Noustriks
                </div>
                <ul className="mkt-noustriks-tree-branches">
                  <li>
                    <Link href="/products/studynexs" className="mkt-noustriks-tree-item mkt-noustriks-tree-item--active">
                      <strong>StudyNexs</strong>
                      <span>AI Operating System for Schools</span>
                    </Link>
                  </li>
                  <li>
                    <Link href="/products/memory-fabric" className="mkt-noustriks-tree-item">
                      <strong>Memory Fabric</strong>
                      <span>Enterprise Memory Platform</span>
                    </Link>
                  </li>
                  <li>
                    <Link href="/research" className="mkt-noustriks-tree-item">
                      <strong>Noustriks Research</strong>
                      <span>AI · Memory · Quantum</span>
                    </Link>
                  </li>
                  <li>
                    <span className="mkt-noustriks-tree-item mkt-noustriks-tree-item--muted">
                      <strong>Noustriks Labs</strong>
                      <span>Experimental Products</span>
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

export function VisionSection() {
  return (
    <section className="mkt-section mkt-section--vision" aria-labelledby="vision-heading">
      <div className="mkt-container">
        <FadeIn className="mkt-vision-block">
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            <Sparkles size={14} aria-hidden />
            Vision
          </div>
          <h2 id="vision-heading" className="mkt-h2">
            {NOUSTRIKS.visionTitle}
          </h2>
          <p className="mkt-lead mkt-vision-lead">{NOUSTRIKS.visionBody}</p>
          <Link href="/company" className="mkt-inline-link mkt-vision-link">
            Read our company story →
          </Link>
        </FadeIn>
      </div>
    </section>
  );
}
