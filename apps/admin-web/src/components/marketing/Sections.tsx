"use client";

import Link from "next/link";
import {
  Brain,
  FileText,
  GraduationCap,
  LineChart,
  MessageSquare,
  Shield,
} from "lucide-react";
import { AnimatedStat } from "./AnimatedStat";
import { FadeIn, MagneticButton } from "./Motion";
import { FOOTER_LINKS, NOUSTRIKS, copyrightNotice, LEGAL } from "@/lib/noustriks-content";

const FEATURES = [
  {
    icon: Brain,
    title: "Concept mastery engine",
    desc: "AI flags weak topics from real exam data and drafts parent-ready narratives teachers approve.",
  },
  {
    icon: FileText,
    title: "AI question papers",
    desc: "Board-style papers in minutes — human-in-the-loop approval before anything reaches students.",
  },
  {
    icon: LineChart,
    title: "Predictive insights",
    desc: "Attendance, fees, and performance signals surfaced before they become crises.",
  },
  {
    icon: MessageSquare,
    title: "Family intelligence",
    desc: "Parents see progress, feedback, and fees — without another app to download.",
  },
  {
    icon: Shield,
    title: "Enterprise trust",
    desc: "Role-based access, audit trails, and tenant isolation built for regulated environments.",
  },
  {
    icon: GraduationCap,
    title: "Full school stack",
    desc: "Admissions to report cards — one operating system, not ten disconnected tools.",
  },
];

export function FeaturesSection() {
  return (
    <section className="mkt-section" id="features" aria-labelledby="features-heading">
      <div className="mkt-container">
        <FadeIn className="mkt-section-header">
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            Capabilities
          </div>
          <h2 id="features-heading" className="mkt-h2">
            AI that works inside your school
          </h2>
          <p className="mkt-lead">
            Not a chatbot bolted on — intelligence woven through every workflow your staff already runs.
          </p>
        </FadeIn>

        <div className="mkt-grid-12">
          {FEATURES.map((f, i) => (
            <FadeIn key={f.title} className="mkt-card mkt-glass mkt-col-4" delay={i * 0.05}>
              <div className="mkt-card-icon">
                <f.icon size={20} strokeWidth={2} aria-hidden />
              </div>
              <h3 className="mkt-h3">{f.title}</h3>
              <p>{f.desc}</p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

const STATS = [
  { value: "40%", label: "Less admin time on papers" },
  { value: "3×", label: "Faster parent communication" },
  { value: "99.9%", label: "Platform uptime SLA" },
  { value: "1", label: "Unified school OS" },
];

export function StatsSection() {
  return (
    <section className="mkt-section mkt-section--stats" aria-label="Impact statistics">
      <div className="mkt-container">
        <div className="mkt-stats">
          {STATS.map((s, i) => (
            <FadeIn key={s.label} delay={i * 0.08}>
              <AnimatedStat value={s.value} label={s.label} />
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

const TESTIMONIALS = [
  {
    quote:
      "We went from spending entire weekends on question papers to approving AI drafts in under an hour. Parents noticed the difference immediately.",
    author: "Priya Sharma",
    role: "Principal, Greenwood Public School",
  },
  {
    quote:
      "The mastery flags catch what I'd miss in a class of forty. I edit the parent note, tap send — done.",
    author: "Rajesh Kumar",
    role: "Maths Teacher, Class 10",
  },
  {
    quote:
      "Finally I can see both my children's progress without calling the school. The weak topics view alone is worth it.",
    author: "Anita Reddy",
    role: "Parent of two",
  },
];

export function TestimonialsSection() {
  return (
    <section className="mkt-section" aria-labelledby="testimonials-heading">
      <div className="mkt-container">
        <FadeIn className="mkt-section-header">
          <h2 id="testimonials-heading" className="mkt-h2">
            Trusted by educators who lead
          </h2>
        </FadeIn>

        <div className="mkt-testimonial-grid">
          {TESTIMONIALS.map((t, i) => (
            <FadeIn key={t.author} delay={i * 0.12}>
              <blockquote className="mkt-card mkt-glass" style={{ margin: 0, height: "100%" }}>
                <p className="mkt-quote">&ldquo;{t.quote}&rdquo;</p>
                <footer className="mkt-quote-author">
                  {t.author}
                  <div className="mkt-quote-role">{t.role}</div>
                </footer>
              </blockquote>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

export function CTASection() {
  return (
    <section className="mkt-section" aria-labelledby="cta-heading">
      <div className="mkt-container">
        <FadeIn>
          <div className="mkt-cta mkt-glass-strong">
            <h2 id="cta-heading" className="mkt-h2" style={{ position: "relative" }}>
              Ready to run your school on intelligence?
            </h2>
            <p className="mkt-lead" style={{ margin: "1rem auto 0", position: "relative" }}>
              Join the pilot program. Full SMS stack, AI papers, and family portals — live in weeks.
            </p>
            <div className="mkt-hero-actions" style={{ position: "relative" }}>
              <MagneticButton href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--lg">
                Request a demo
              </MagneticButton>
              <MagneticButton href="/pricing" className="mkt-btn mkt-btn--glass mkt-btn--lg">
                View pricing
              </MagneticButton>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

export function MarketingFooter() {
  return (
    <footer className="mkt-footer mkt-footer--premium">
      <div className="mkt-container">
        <div className="mkt-footer-grid mkt-footer-grid--premium">
          <div className="mkt-footer-brand">
            <Link href="/products" className="mkt-nav-logo mkt-nav-logo--noustriks" style={{ padding: 0, marginBottom: "1rem" }}>
              <span className="mkt-nav-logo-mark mkt-nav-logo-mark--noustriks" aria-hidden>
                N
              </span>
              {NOUSTRIKS.name}
            </Link>
            <p className="mkt-footer-tagline">{NOUSTRIKS.tagline}</p>
            <p className="mkt-footer-studynexs-note">
              <Link href="/">StudyNexs</Link> is a flagship product of Noustriks.
            </p>
          </div>
          <div>
            <h4>Products</h4>
            {FOOTER_LINKS.products.map((link) => (
              <Link key={link.href} href={link.href}>
                {link.label}
              </Link>
            ))}
          </div>
          <div>
            <h4>StudyNexs</h4>
            {FOOTER_LINKS.studynexs.map((link) => (
              <Link key={link.href} href={link.href}>
                {link.label}
              </Link>
            ))}
            <Link href="/login?portal=parent">Parent portal</Link>
            <Link href="/login?portal=student">Student portal</Link>
          </div>
          <div>
            <h4>Company</h4>
            {FOOTER_LINKS.company.map((link) => (
              <Link key={link.href} href={link.href}>
                {link.label}
              </Link>
            ))}
            <Link href="/login">Sign in</Link>
            <Link href="/pricing">Pricing</Link>
          </div>
        </div>
        <div className="mkt-footer-bottom">
          <span>{copyrightNotice()}</span>
          <span>
            {LEGAL.productLine} · {LEGAL.company} · Owner {LEGAL.owner} ({LEGAL.ownerAlias}) ·{" "}
            {LEGAL.license}
          </span>
        </div>
      </div>
    </footer>
  );
}
