"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Script from "next/script";
import { API_URL, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { setDemoSessionToken, setProspectTenantSlug } from "@/lib/tenant";

type DemoSessionResponse = {
  data: {
    tenant_slug: string;
    access_token: string;
    session_token: string;
    expires_at: string;
    onboarding_path: string;
    school_name: string;
  };
};

declare global {
  interface Window {
    turnstile?: {
      render: (
        el: HTMLElement,
        opts: {
          sitekey: string;
          callback: (token: string) => void;
          "error-callback"?: () => void;
          "expired-callback"?: () => void;
        }
      ) => string;
      reset: (widgetId: string) => void;
    };
  }
}

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY?.trim() || "";

export default function DemoStartPage() {
  const router = useRouter();
  const { loginWithTokens } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schoolName, setSchoolName] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const turnstileRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);

  const mountTurnstile = useCallback(() => {
    if (!TURNSTILE_SITE_KEY || !turnstileRef.current || !window.turnstile) return;
    if (widgetIdRef.current) return;
    widgetIdRef.current = window.turnstile.render(turnstileRef.current, {
      sitekey: TURNSTILE_SITE_KEY,
      callback: (token: string) => setTurnstileToken(token),
      "expired-callback": () => setTurnstileToken(null),
      "error-callback": () => setTurnstileToken(null),
    });
  }, []);

  useEffect(() => {
    mountTurnstile();
  }, [mountTurnstile]);

  const startDemo = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (TURNSTILE_SITE_KEY && !turnstileToken) {
        throw new Error("Please complete the verification check below.");
      }
      const body: Record<string, string> = {};
      if (schoolName.trim()) body.display_name = schoolName.trim();
      if (turnstileToken) body.turnstile_token = turnstileToken;

      const res = await fetch(`${API_URL}/api/v1/demo/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        const detail =
          typeof payload.detail === "string"
            ? payload.detail
            : "Could not start your demo. Please try again in a moment.";
        throw new Error(detail);
      }
      const json = (await res.json()) as DemoSessionResponse;
      const session = json.data;
      setProspectTenantSlug(session.tenant_slug);
      setDemoSessionToken(session.session_token);
      await loginWithTokens({ access_token: session.access_token });
      router.push(session.onboarding_path);
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not start your demo school."));
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.reset(widgetIdRef.current);
        setTurnstileToken(null);
      }
    } finally {
      setLoading(false);
    }
  }, [loginWithTokens, router, schoolName, turnstileToken]);

  return (
    <main className="sn-app sn-app--dark min-h-screen flex items-center justify-center p-6">
      {TURNSTILE_SITE_KEY ? (
        <Script
          src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
          strategy="afterInteractive"
          onLoad={mountTurnstile}
        />
      ) : null}
      <div className="sn-workspace sn-workspace--primary max-w-lg w-full p-8 space-y-6">
        <header className="space-y-2">
          <p className="text-sm text-[var(--text-muted)]">StudyNexs prospect demo</p>
          <h1 className="text-2xl font-semibold text-[var(--text-primary)]">
            Teach StudyNexs your curriculum
          </h1>
          <p className="text-[var(--text-secondary)]">
            We&apos;ll create a private demo school just for you. Paste your syllabus or chapter
            list, review the draft pack, and unlock grounded AI — no shared data with other
            visitors.
          </p>
        </header>

        <label className="block space-y-2">
          <span className="text-sm text-[var(--text-secondary)]">School name (optional)</span>
          <input
            type="text"
            maxLength={80}
            value={schoolName}
            onChange={(e) => setSchoolName(e.target.value)}
            placeholder="e.g. Riverside High School"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--sn-glass-c)] px-3 py-2 text-[var(--text-primary)]"
            disabled={loading}
          />
        </label>

        {TURNSTILE_SITE_KEY ? (
          <div ref={turnstileRef} className="min-h-[65px]" data-testid="demo-turnstile" />
        ) : null}

        {error ? (
          <p className="text-sm text-[var(--danger)]" role="alert">
            {error}
          </p>
        ) : null}

        <button
          type="button"
          onClick={() => void startDemo()}
          disabled={loading || (Boolean(TURNSTILE_SITE_KEY) && !turnstileToken)}
          className="w-full rounded-lg bg-[var(--accent)] px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {loading ? "Creating your demo school…" : "Start my demo"}
        </button>

        <p className="text-xs text-[var(--text-muted)]">
          Demo schools stay active for up to 72 hours, then expire automatically. Your session is
          isolated — paid pilot schools are never modified.
        </p>
      </div>
    </main>
  );
}
