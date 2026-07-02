"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { apiAuth, getAccessTokenFromAuthResponse, getApiErrorMessage } from "@/lib/api";
import { DEMO_LOGINS, DemoPortalKey, homePathAfterLogin } from "@/lib/portal";
import { ArrowLeft, Lock, RotateCcw, Smartphone } from "lucide-react";
import { DemoDataBanner } from "@/components/DemoDataBanner";

type Step = "method" | "mobile" | "otp" | "password";

function LoginPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loginWithTokens } = useAuth();
  const reduce = useReducedMotion();

  const [step, setStep] = useState<Step>("method");
  const [portalTab, setPortalTab] = useState<DemoPortalKey>("staff");
  const [mobile, setMobile] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [maskedMobile, setMaskedMobile] = useState("");
  const [devOtp, setDevOtp] = useState("");

  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  const applyPortalFromQuery = (portal: string | null) => {
    if (portal === "parent" || portal === "student" || portal === "teacher" || portal === "staff") {
      setPortalTab(portal);
      setStep("password");
      const creds = DEMO_LOGINS[portal];
      setUsername(creds.username);
      setPassword(creds.password);
    }
  };

  useEffect(() => {
    const fromRouter = searchParams.get("portal");
    if (fromRouter) {
      applyPortalFromQuery(fromRouter);
      return;
    }
    // Fallback: useSearchParams can lag behind the URL on first client paint (e2e / deep links).
    if (typeof window !== "undefined") {
      applyPortalFromQuery(new URLSearchParams(window.location.search).get("portal"));
    }
  }, [searchParams]);

  const applyPortalTab = (key: DemoPortalKey) => {
    setPortalTab(key);
    const creds = DEMO_LOGINS[key];
    setUsername(creds.username);
    setPassword(creds.password);
    setStep("password");
    setError("");
  };

  const redirectHome = async () => {
    router.push(await homePathAfterLogin());
  };

  const handleSendOtp = async () => {
    setError("");
    if (!mobile.trim()) {
      setError("Please enter your mobile number");
      return;
    }
    const formatted = mobile.startsWith("+") ? mobile : `+91${mobile}`;
    setLoading(true);
    try {
      const r = await apiAuth.sendOtp(formatted);
      setMaskedMobile(r.masked_mobile || r.data?.masked_mobile || formatted);
      const dev = r.dev_otp || r.data?.dev_otp;
      if (dev) setDevOtp(dev);
      setStep("otp");
    } catch (e: unknown) {
      setError(getApiErrorMessage(e, "Failed to send OTP"));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    setError("");
    const code = otp.join("");
    if (code.length < 6) {
      setError("Please enter the 6-digit OTP");
      return;
    }
    const formatted = mobile.startsWith("+") ? mobile : `+91${mobile}`;
    setLoading(true);
    try {
      const r = (await apiAuth.verifyOtp(formatted, code)) as Record<string, unknown>;
      const token = getAccessTokenFromAuthResponse(r);
      if (!token) {
        setError("Login succeeded but no access token was returned.");
        return;
      }
      try {
        await loginWithTokens({ access_token: token });
      } catch (e: unknown) {
        setError(getApiErrorMessage(e, "Login succeeded but profile could not be loaded."));
        return;
      }
      router.push(await homePathAfterLogin());
    } catch (e: unknown) {
      setError(getApiErrorMessage(e, "Could not verify OTP. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async () => {
    setError("");
    if (!username.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);
    try {
      await login(username, password);
      await redirectHome();
    } catch (e: unknown) {
      setError(getApiErrorMessage(e, "Invalid credentials"));
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...otp];
    next[index] = value.slice(-1);
    setOtp(next);
    if (value && index < 5) otpRefs.current[index + 1]?.focus();
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const cardAnim = reduce
    ? {}
    : {
        initial: { y: 20, filter: "blur(8px)" },
        animate: { y: 0, filter: "blur(0px)" },
        transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
      };

  return (
    <div className="mkt-login-page">
      <DemoDataBanner variant="marketing" />
      <motion.div className="mkt-login-card mkt-glass-strong" {...cardAnim}>
        {step === "method" && (
          <Link href="/" className="mkt-login-back">
            <ArrowLeft size={14} aria-hidden />
            Back to home
          </Link>
        )}

        {step === "method" && (
          <>
            <h1 className="mkt-h3" style={{ fontSize: "1.65rem", marginBottom: "0.35rem" }}>
              Welcome back
            </h1>
            <p style={{ color: "var(--mkt-gray-500)", fontSize: "0.9rem", marginBottom: "1.75rem" }}>
              Sign in to your StudyNexs portal
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <button
                type="button"
                className="mkt-btn mkt-btn--glass"
                style={{ justifyContent: "flex-start", padding: "1rem 1.15rem", width: "100%" }}
                onClick={() => setStep("mobile")}
              >
                <Smartphone size={18} style={{ color: "var(--mkt-blue-500)" }} aria-hidden />
                <span style={{ textAlign: "left" }}>
                  <span style={{ display: "block", fontWeight: 600 }}>Mobile OTP</span>
                  <span style={{ fontSize: "0.78rem", color: "var(--mkt-gray-500)" }}>
                    Admins, teachers & parents
                  </span>
                </span>
              </button>
              <button
                type="button"
                className="mkt-btn mkt-btn--glass"
                style={{ justifyContent: "flex-start", padding: "1rem 1.15rem", width: "100%" }}
                onClick={() => setStep("password")}
              >
                <Lock size={18} style={{ color: "var(--mkt-navy-soft)" }} aria-hidden />
                <span style={{ textAlign: "left" }}>
                  <span style={{ display: "block", fontWeight: 600 }}>Username & password</span>
                  <span style={{ fontSize: "0.78rem", color: "var(--mkt-gray-500)" }}>
                    Students & demo accounts
                  </span>
                </span>
              </button>
            </div>
          </>
        )}

        {step === "mobile" && (
          <>
            <button
              type="button"
              className="mkt-login-back"
              style={{ border: "none", background: "none", cursor: "pointer", padding: 0 }}
              onClick={() => {
                setStep("method");
                setError("");
              }}
            >
              <ArrowLeft size={14} /> Back
            </button>
            <h1 className="mkt-h3" style={{ fontSize: "1.5rem" }}>
              Enter your mobile
            </h1>
            <p style={{ color: "var(--mkt-gray-500)", fontSize: "0.88rem", margin: "0.5rem 0 1.25rem" }}>
              We&apos;ll send a 6-digit OTP
            </p>
            <div className="mkt-form-group">
              <label className="mkt-form-label" htmlFor="mobile-input">
                Mobile number
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <div
                  className="mkt-form-input"
                  style={{ width: "auto", padding: "0.75rem 0.85rem", fontWeight: 600 }}
                >
                  +91
                </div>
                <input
                  id="mobile-input"
                  className="mkt-form-input"
                  type="tel"
                  placeholder="98765 43210"
                  value={mobile.replace("+91", "")}
                  onChange={(e) => {
                    setError("");
                    setMobile(e.target.value);
                  }}
                  onKeyDown={(e) => e.key === "Enter" && handleSendOtp()}
                  maxLength={10}
                  autoFocus
                />
              </div>
            </div>
            {error && <p style={{ color: "#e5484d", fontSize: "0.85rem", marginBottom: "1rem" }}>{error}</p>}
            <button
              type="button"
              className="mkt-btn mkt-btn--primary mkt-btn--block"
              onClick={handleSendOtp}
              disabled={loading}
            >
              {loading ? "Sending…" : "Send OTP"}
            </button>
          </>
        )}

        {step === "otp" && (
          <>
            <button
              type="button"
              className="mkt-login-back"
              style={{ border: "none", background: "none", cursor: "pointer", padding: 0 }}
              onClick={() => {
                setStep("mobile");
                setError("");
              }}
            >
              <ArrowLeft size={14} /> Back
            </button>
            <h1 className="mkt-h3" style={{ fontSize: "1.5rem" }}>
              Enter OTP
            </h1>
            <p style={{ color: "var(--mkt-gray-500)", fontSize: "0.88rem", margin: "0.5rem 0 1.25rem" }}>
              Sent to <strong>{maskedMobile}</strong>
              {devOtp && (
                <span style={{ display: "block", marginTop: 4, color: "var(--mkt-blue-500)", fontWeight: 600 }}>
                  DEV: {devOtp}
                </span>
              )}
            </p>
            <div className="otp-digits" style={{ marginBottom: "1.25rem" }}>
              {otp.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => {
                    otpRefs.current[i] = el;
                  }}
                  className="otp-digit mkt-form-input"
                  style={{ width: 44, height: 52, textAlign: "center", padding: 0 }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => {
                    setError("");
                    handleOtpChange(i, e.target.value);
                  }}
                  onKeyDown={(e) => handleOtpKeyDown(i, e)}
                  autoFocus={i === 0}
                  aria-label={`OTP digit ${i + 1}`}
                />
              ))}
            </div>
            {error && <p style={{ color: "#e5484d", fontSize: "0.85rem", marginBottom: "1rem" }}>{error}</p>}
            <button
              type="button"
              className="mkt-btn mkt-btn--primary mkt-btn--block"
              onClick={handleVerifyOtp}
              disabled={loading}
            >
              {loading ? "Verifying…" : "Verify & sign in"}
            </button>
            <button
              type="button"
              className="mkt-btn mkt-btn--ghost mkt-btn--block"
              style={{ marginTop: "0.65rem" }}
              onClick={() => {
                setOtp(["", "", "", "", "", ""]);
                handleSendOtp();
              }}
            >
              <RotateCcw size={14} aria-hidden /> Resend OTP
            </button>
          </>
        )}

        {step === "password" && (
          <>
            <button
              type="button"
              className="mkt-login-back"
              style={{ border: "none", background: "none", cursor: "pointer", padding: 0 }}
              onClick={() => {
                setStep("method");
                setError("");
              }}
            >
              <ArrowLeft size={14} /> Back
            </button>
            <h1 className="mkt-h3" style={{ fontSize: "1.5rem" }}>
              Sign in
            </h1>
            <p style={{ color: "var(--mkt-gray-500)", fontSize: "0.88rem", margin: "0.5rem 0 1rem" }}>
              Demo logins — select a portal
            </p>

            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.4rem",
                marginBottom: "1rem",
              }}
              role="tablist"
            >
              {(Object.keys(DEMO_LOGINS) as DemoPortalKey[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  role="tab"
                  aria-selected={portalTab === key}
                  className={`mkt-btn mkt-btn--sm${portalTab === key ? " mkt-btn--primary" : " mkt-btn--glass"}`}
                  onClick={() => applyPortalTab(key)}
                >
                  {key === "staff" ? "Admin" : key.charAt(0).toUpperCase() + key.slice(1)}
                </button>
              ))}
            </div>
            <p style={{ fontSize: "0.78rem", color: "var(--mkt-gray-500)", marginBottom: "1rem" }}>
              {DEMO_LOGINS[portalTab].label} · <code>{DEMO_LOGINS[portalTab].username}</code>
            </p>

            <div className="mkt-form-group">
              <label className="mkt-form-label" htmlFor="username-input">
                Username
              </label>
              <input
                id="username-input"
                className="mkt-form-input"
                placeholder="firstname.lastname"
                value={username}
                onChange={(e) => {
                  setError("");
                  setUsername(e.target.value);
                }}
                autoFocus
              />
            </div>
            <div className="mkt-form-group">
              <label className="mkt-form-label" htmlFor="password-input">
                Password
              </label>
              <input
                id="password-input"
                className="mkt-form-input"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => {
                  setError("");
                  setPassword(e.target.value);
                }}
                onKeyDown={(e) => e.key === "Enter" && handlePasswordLogin()}
              />
            </div>

            {error && <p style={{ color: "#e5484d", fontSize: "0.85rem", marginBottom: "1rem" }}>{error}</p>}

            <button
              type="button"
              className="mkt-btn mkt-btn--primary mkt-btn--block"
              onClick={handlePasswordLogin}
              disabled={loading || !username || !password}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </>
        )}
      </motion.div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="mkt-login-page">
          <div className="spinner" />
        </div>
      }
    >
      <LoginPageInner />
    </Suspense>
  );
}
