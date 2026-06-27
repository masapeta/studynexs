"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  Brain,
  FileText,
  GraduationCap,
  LineChart,
  MessageSquare,
  Shield,
  Sparkles,
} from "lucide-react";
import { AnimatedStat } from "./AnimatedStat";
import { HeroDashboardScene } from "./HeroDashboardScene";
import { FadeIn, MagneticButton } from "./Motion";

export function HeroSection() {
  const reduce = useReducedMotion();

  return (
    <section className="mkt-hero" aria-labelledby="hero-heading">
      <div className="mkt-hero-grid">
        <div className="mkt-hero-copy">
          <motion.div
            className="mkt-eyebrow mkt-glass"
            initial={reduce ? false : { opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            <Sparkles size={14} aria-hidden />
            AI-Powered School OS
          </motion.div>

          <motion.h1
            id="hero-heading"
            className="mkt-h1 mkt-h1--hero"
            initial={reduce ? false : { opacity: 0, y: 32, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.85, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            The world&apos;s most advanced
            <br />
            <span className="mkt-gradient-text">school operating system</span>
          </motion.h1>

          <motion.p
            className="mkt-lead mkt-lead--hero"
            initial={reduce ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45 }}
          >
            Immersive intelligence for principals, teachers, students, and parents — one glass
            platform where AI assists, humans approve, and every school stays in control.
          </motion.p>

          <motion.div
            className="mkt-hero-actions mkt-hero-actions--left"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.6 }}
          >
            <MagneticButton href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--lg">
              Start free pilot
            </MagneticButton>
            <MagneticButton href="/platform" className="mkt-btn mkt-btn--glass mkt-btn--lg">
              Explore platform
            </MagneticButton>
          </motion.div>
        </div>

        <motion.div
          className="mkt-hero-visual"
          initial={reduce ? false : { opacity: 0, y: 48, rotateX: 8 }}
          animate={{ opacity: 1, y: 0, rotateX: 4 }}
          transition={{ duration: 1, delay: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          <HeroDashboardScene />
        </motion.div>
      </div>
    </section>
  );
}

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
    <footer className="mkt-footer">
      <div className="mkt-container">
        <div className="mkt-footer-grid">
          <div>
            <Link href="/" className="mkt-nav-logo" style={{ padding: 0, marginBottom: "1rem" }}>
              <span className="mkt-nav-logo-mark">SN</span>
              StudyNexs
            </Link>
            <p style={{ fontSize: "0.88rem", color: "var(--mkt-gray-500)", maxWidth: "20rem", lineHeight: 1.65 }}>
              The AI-powered school operating system for principals, teachers, students, and parents.
            </p>
          </div>
          <div>
            <h4>Product</h4>
            <Link href="/platform">Platform</Link>
            <Link href="/#features">Features</Link>
            <Link href="/pricing">Pricing</Link>
          </div>
          <div>
            <h4>Portals</h4>
            <Link href="/login?portal=staff">Admin</Link>
            <Link href="/login?portal=teacher">Teacher</Link>
            <Link href="/login?portal=parent">Parent</Link>
            <Link href="/login?portal=student">Student</Link>
          </div>
          <div>
            <h4>Company</h4>
            <Link href="/login">Sign in</Link>
            <a href="mailto:hello@studynexs.com">Contact</a>
          </div>
        </div>
        <div className="mkt-footer-bottom">
          <span>© {new Date().getFullYear()} StudyNexs. All rights reserved.</span>
          <span>Built for Indian K-12 · Privacy-first · SOC-ready architecture</span>
        </div>
      </div>
    </footer>
  );
}
