"use client";

import Link from "next/link";
import { Mail, MessageSquare } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { FadeIn } from "@/components/marketing/Motion";
import { MarketingFooter } from "@/components/marketing/Sections";
import { CONTACT } from "@/lib/noustriks-content";

export default function ContactPage() {
  return (
    <main>
      <MarketingPageHero
        id="contact-heading"
        compact
        eyebrow={
          <>
            <MessageSquare size={14} aria-hidden />
            Contact
          </>
        }
        title={
          <>
            {CONTACT.headline}
          </>
        }
        lead={CONTACT.description}
      />

      <section className="mkt-section" aria-labelledby="contact-options">
        <div className="mkt-container mkt-contact-grid">
          <FadeIn className="mkt-contact-card mkt-glass-strong">
            <h2 id="contact-options" className="mkt-h3">
              General inquiries
            </h2>
            <p>For schools, enterprises, partners, and press.</p>
            <a href={`mailto:${CONTACT.email}`} className="mkt-contact-email">
              <Mail size={18} aria-hidden />
              {CONTACT.email}
            </a>
          </FadeIn>
          <FadeIn delay={0.1} className="mkt-contact-card mkt-glass">
            <h2 className="mkt-h3">StudyNexs demo</h2>
            <p>Principals and school leadership evaluating the AI School OS.</p>
            <Link href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--block">
              Request a demo
            </Link>
          </FadeIn>
          <FadeIn delay={0.15} className="mkt-contact-card mkt-glass">
            <h2 className="mkt-h3">Memory Fabric</h2>
            <p>Enterprise teams exploring persistent memory infrastructure.</p>
            <a href={`mailto:${CONTACT.email}?subject=Memory%20Fabric%20inquiry`} className="mkt-btn mkt-btn--glass mkt-btn--block">
              Email our team
            </a>
          </FadeIn>
        </div>
      </section>

      <MarketingFooter />
    </main>
  );
}
