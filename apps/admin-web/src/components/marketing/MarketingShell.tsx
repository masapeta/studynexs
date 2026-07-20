"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { PlatformMark } from "@/components/brand/PlatformMark";
import { NAV_LINKS, NOUSTRIKS } from "@/lib/noustriks-content";
import { NeuralCanvas } from "./NeuralCanvas";

function isNavActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function MarketingBackground() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-bg" aria-hidden>
      <div className="mkt-mesh" />
      <div className="mkt-grid-fade" />
      <NeuralCanvas />
      {!reduce && (
        <>
          <div className="mkt-orb mkt-orb--1" />
          <div className="mkt-orb mkt-orb--2" />
          <div className="mkt-orb mkt-orb--3" />
        </>
      )}
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

  useEffect(() => {
    document.body.classList.toggle("mkt-nav-menu-open", mobileOpen);
    return () => document.body.classList.remove("mkt-nav-menu-open");
  }, [mobileOpen]);

  return (
    <>
      <motion.header
        className={`mkt-nav-wrap${scrolled ? " mkt-nav-wrap--scrolled" : ""}`}
        initial={reduce ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      >
        <nav
          className={`mkt-nav mkt-nav--chips${scrolled ? " mkt-nav--scrolled" : ""}`}
          aria-label="Main"
        >
          <div className="mkt-nav-chip mkt-nav-chip--ghost mkt-nav-chip--brand">
            <Link href="/" className="mkt-nav-logo mkt-nav-logo--noustriks">
              <PlatformMark variant="noustriks" size="sm" />
              {NOUSTRIKS.name}
            </Link>
          </div>

          <div className="mkt-nav-group mkt-nav-group--links" role="list">
            {NAV_LINKS.map((link) => {
              const active = isNavActive(pathname, link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  role="listitem"
                  className={`mkt-nav-chip mkt-nav-chip--link mkt-glass-nav mkt-nav-link${
                    active ? " mkt-nav-chip--active" : ""
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          <div className="mkt-nav-group mkt-nav-group--cta">
            <Link
              href="/login"
              className="mkt-nav-chip mkt-nav-chip--link mkt-glass-nav mkt-nav-link mkt-nav-link--hide-mobile"
            >
              Sign in
            </Link>
            <Link
              href="/login?portal=staff"
              className="mkt-btn mkt-btn--primary mkt-btn--sm mkt-nav-cta-btn"
            >
              Request demo
            </Link>
          </div>
        </nav>
        <button
          type="button"
          className="mkt-nav-chip mkt-nav-chip--menu mkt-nav-mobile-btn"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((o) => !o)}
        >
          {mobileOpen ? <X size={16} strokeWidth={2.25} /> : <Menu size={16} strokeWidth={2.25} />}
        </button>
      </motion.header>

      {mobileOpen && (
        <button
          type="button"
          className="mkt-mobile-backdrop"
          aria-label="Close menu"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div
        className={`mkt-mobile-menu${mobileOpen ? " mkt-mobile-menu--open" : ""}`}
        role="dialog"
        aria-label="Mobile navigation"
        aria-hidden={!mobileOpen}
      >
        <div className="mkt-mobile-menu-panel mkt-glass-strong">
          {NAV_LINKS.map((link) => {
            const active = isNavActive(pathname, link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`mkt-mobile-menu-link${active ? " mkt-mobile-menu-link--active" : ""}`}
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            );
          })}
          <div className="mkt-mobile-menu-divider" aria-hidden />
          <Link href="/login" className="mkt-mobile-menu-link" onClick={() => setMobileOpen(false)}>
            Sign in
          </Link>
          <Link
            href="/login?portal=staff"
            className="mkt-btn mkt-btn--primary mkt-btn--block"
            onClick={() => setMobileOpen(false)}
          >
            Request demo
          </Link>
        </div>
      </div>
    </>
  );
}
