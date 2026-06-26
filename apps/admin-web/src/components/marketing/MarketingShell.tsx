"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { Menu, X } from "lucide-react";

const LINKS = [
  { href: "/platform", label: "Platform" },
  { href: "/pricing", label: "Pricing" },
  { href: "/#roles", label: "Solutions" },
];

export function MarketingBackground() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-bg" aria-hidden>
      <div className="mkt-mesh" />
      <div className={`mkt-orb mkt-orb--1${reduce ? "" : ""}`} />
      <div className="mkt-orb mkt-orb--2" />
      <div className="mkt-orb mkt-orb--3" />
    </div>
  );
}

export function MarketingNav() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <>
      <motion.header
        className="mkt-nav-wrap"
        initial={reduce ? false : { opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      >
        <nav className={`mkt-nav mkt-glass${scrolled ? " mkt-nav--scrolled" : ""}`} aria-label="Main">
          <Link href="/" className="mkt-nav-logo">
            <span className="mkt-nav-logo-mark" aria-hidden>
              SN
            </span>
            StudyNexs
          </Link>

          <div className="mkt-nav-links">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`mkt-nav-link${
                  pathname === link.href || (link.href.startsWith("/#") && pathname === "/")
                    ? " mkt-nav-link--active"
                    : ""
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="mkt-nav-cta">
            <Link href="/login" className="mkt-nav-link">
              Sign in
            </Link>
            <Link href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--sm">
              Request demo
            </Link>
            <button
              type="button"
              className="mkt-nav-mobile-btn"
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              onClick={() => setMobileOpen((o) => !o)}
            >
              {mobileOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </nav>
      </motion.header>

      <div className={`mkt-mobile-menu${mobileOpen ? " mkt-mobile-menu--open" : ""}`} role="dialog" aria-hidden={!mobileOpen}>
        {LINKS.map((link) => (
          <Link key={link.href} href={link.href} onClick={() => setMobileOpen(false)}>
            {link.label}
          </Link>
        ))}
        <Link href="/login" onClick={() => setMobileOpen(false)}>
          Sign in
        </Link>
        <Link href="/login?portal=staff" onClick={() => setMobileOpen(false)}>
          Request demo
        </Link>
      </div>
    </>
  );
}
