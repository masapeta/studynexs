"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiAuth, getAccessTokenFromAuthResponse, getApiErrorMessage } from "@/lib/api";
import { DEMO_LOGINS, DemoPortalKey, homePathAfterLogin } from "@/lib/portal";
import { Smartphone, Lock, ChevronRight, RotateCcw } from "lucide-react";

type Step = "method" | "mobile" | "otp" | "password";

function LoginPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loginWithTokens } = useAuth();

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

  useEffect(() => {
    const p = searchParams.get("portal");
    if (p === "parent" || p === "student" || p === "teacher" || p === "staff") {
      setPortalTab(p);
      setStep("password");
      const creds = DEMO_LOGINS[p];
      setUsername(creds.username);
      setPassword(creds.password);
    }
  }, [searchParams]);

  const applyPortalTab = (key: DemoPortalKey) => {
    setPortalTab(key);
    const creds = DEMO_LOGINS[key];
    setUsername(creds.username);
    setPassword(creds.password);
    setStep("password");
    clearError();
  };

  const clearError = () => setError("");

  const redirectHome = async () => {
    router.push(await homePathAfterLogin());
  };

  // ── Step 1: Send OTP ──────────────────────────────────────────────────────
  const handleSendOtp = async () => {
    clearError();
    if (!mobile.trim()) { setError("Please enter your mobile number"); return; }
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
    } finally { setLoading(false); }
  };

  // ── Step 2: Verify OTP ────────────────────────────────────────────────────
  const handleVerifyOtp = async () => {
    clearError();
    const code = otp.join("");
    if (code.length < 6) { setError("Please enter the 6-digit OTP"); return; }
    const formatted = mobile.startsWith("+") ? mobile : `+91${mobile}`;
    setLoading(true);
    try {
      const r = await apiAuth.verifyOtp(formatted, code) as Record<string, unknown>;
      const token = getAccessTokenFromAuthResponse(r);
      if (!token) {
        setError("Login succeeded but no access token was returned.");
        return;
      }
      try {
        await loginWithTokens({ access_token: token });
      } catch (e: unknown) {
        setError(getApiErrorMessage(e, "Login succeeded but profile could not be loaded. Please try again."));
        return;
      }
      router.push(await homePathAfterLogin());
    } catch (e: unknown) {
      setError(getApiErrorMessage(e, "Could not verify OTP. Please try again."));
    } finally { setLoading(false); }
  };

  // ── Password Login ────────────────────────────────────────────────────────
  const handlePasswordLogin = async () => {
    clearError();
    if (!username.trim() || !password.trim()) { setError("Please fill in all fields"); return; }
    setLoading(true);
    try {
      await login(username, password);
      await redirectHome();
    } catch (e: unknown) {
      setError(getApiErrorMessage(e, "Invalid credentials"));
    } finally { setLoading(false); }
  };

  // ── OTP input handler ─────────────────────────────────────────────────────
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

  return (
    <div className="login-page">
      {/* Left Brand Panel */}
      <div className="login-left">
        <div className="login-brand">
          <div style={{ marginBottom: 28 }}>
            <Image
              src="/studynexs.png"
              alt="StudyNexs"
              width={220}
              height={70}
              style={{ objectFit: "contain", filter: "brightness(0) invert(1)" }}
              priority
            />
          </div>
          <div className="login-brand-tagline">
            The complete school management platform for modern educators.
          </div>
          <div className="login-features">
            {["Real-time attendance tracking", "Smart fee management", "Parent-teacher communication", "Academic performance analytics"].map(f => (
              <div key={f} className="login-feature">
                <div className="login-feature-dot" />
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="login-right">
        <div className="login-form-wrap">

          {/* Method selection */}
          {step === "method" && (
            <>
              <h1 className="login-heading">Welcome back</h1>
              <p className="login-subheading">Sign in to your StudyNexs account</p>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <button
                  id="btn-otp-login"
                  className="btn btn-outline btn-lg"
                  style={{ justifyContent: "flex-start", gap: 14, padding: "14px 18px", width: "100%" }}
                  onClick={() => setStep("mobile")}
                >
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: "#eef2ff", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Smartphone size={18} color="#2563eb" />
                  </div>
                  <div style={{ textAlign: "left", flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#0f172a" }}>Mobile OTP</div>
                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 1 }}>For admins, teachers & parents</div>
                  </div>
                  <ChevronRight size={16} color="#94a3b8" />
                </button>

                <button
                  id="btn-password-login"
                  className="btn btn-outline btn-lg"
                  style={{ justifyContent: "flex-start", gap: 14, padding: "14px 18px", width: "100%" }}
                  onClick={() => setStep("password")}
                >
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: "#f0fdf4", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Lock size={18} color="#059669" />
                  </div>
                  <div style={{ textAlign: "left", flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#0f172a" }}>Username & Password</div>
                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 1 }}>For students & admins</div>
                  </div>
                  <ChevronRight size={16} color="#94a3b8" />
                </button>
              </div>
            </>
          )}

          {/* Mobile OTP — enter mobile */}
          {step === "mobile" && (
            <>
              <button className="btn btn-ghost btn-sm" style={{ marginBottom: 16, paddingLeft: 0 }} onClick={() => { setStep("method"); clearError(); }}>
                ← Back
              </button>
              <h1 className="login-heading">Enter your mobile</h1>
              <p className="login-subheading">We&apos;ll send a 6-digit OTP to verify it&apos;s you</p>

              <div className="form-group" style={{ marginBottom: 20 }}>
                <label className="form-label" htmlFor="mobile-input">Mobile Number</label>
                <div style={{ display: "flex", gap: 8 }}>
                  <div style={{ display: "flex", alignItems: "center", padding: "10px 13px", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", color: "var(--text-secondary)", fontSize: 14, fontWeight: 600, background: "var(--bg)", whiteSpace: "nowrap" }}>+91</div>
                  <input
                    id="mobile-input"
                    className="form-input"
                    type="tel"
                    placeholder="98765 43210"
                    value={mobile.replace("+91", "")}
                    onChange={e => { clearError(); setMobile(e.target.value); }}
                    onKeyDown={e => e.key === "Enter" && handleSendOtp()}
                    maxLength={10}
                    autoFocus
                  />
                </div>
              </div>

              {error && <p style={{ color: "var(--danger)", fontSize: 13, marginBottom: 16 }}>{error}</p>}

              <button id="btn-send-otp" className="btn btn-primary btn-lg" style={{ width: "100%" }} onClick={handleSendOtp} disabled={loading}>
                {loading ? "Sending…" : "Send OTP"}
              </button>
            </>
          )}

          {/* OTP Entry */}
          {step === "otp" && (
            <>
              <h1 className="login-heading">Enter OTP</h1>
              <p className="login-subheading">
                Sent to <strong>{maskedMobile}</strong>
                {devOtp && <span style={{ display: "block", marginTop: 4, fontSize: 12, color: "var(--success)", fontWeight: 600 }}>DEV: {devOtp}</span>}
              </p>

              <div style={{ marginBottom: 24, marginTop: 8 }}>
                <div className="otp-digits">
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      id={`otp-${i}`}
                      ref={(el) => { otpRefs.current[i] = el; }}
                      className="otp-digit"
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={e => { clearError(); handleOtpChange(i, e.target.value); }}
                      onKeyDown={e => handleOtpKeyDown(i, e)}
                      autoFocus={i === 0}
                    />
                  ))}
                </div>
              </div>

              {error && <p style={{ color: "var(--danger)", fontSize: 13, marginBottom: 16 }}>{error}</p>}

              <button id="btn-verify-otp" className="btn btn-primary btn-lg" style={{ width: "100%", marginBottom: 14 }} onClick={handleVerifyOtp} disabled={loading}>
                {loading ? "Verifying…" : "Verify & Sign In"}
              </button>

              <button className="btn btn-ghost" style={{ width: "100%", justifyContent: "center", gap: 6 }} onClick={() => { setOtp(["", "", "", "", "", ""]); handleSendOtp(); }}>
                <RotateCcw size={13} /> Resend OTP
              </button>
            </>
          )}

          {/* Username + Password */}
          {step === "password" && (
            <>
              <button className="btn btn-ghost btn-sm" style={{ marginBottom: 16, paddingLeft: 0 }} onClick={() => { setStep("method"); clearError(); }}>
                ← Back
              </button>
              <h1 className="login-heading">Sign In</h1>
              <p className="login-subheading">Demo logins — tap a portal, then sign in</p>

              <div className="portal-login-tabs">
                {(Object.keys(DEMO_LOGINS) as DemoPortalKey[]).map((key) => (
                  <button
                    key={key}
                    type="button"
                    className={`portal-login-tab${portalTab === key ? " active" : ""}`}
                    onClick={() => applyPortalTab(key)}
                  >
                    {key === "staff" ? "Admin" : key.charAt(0).toUpperCase() + key.slice(1)}
                  </button>
                ))}
              </div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16 }}>
                {DEMO_LOGINS[portalTab].label} · <code>{DEMO_LOGINS[portalTab].username}</code>
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 20 }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="username-input" style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Username</label>
                  <input id="username-input" className="form-input" placeholder="firstname.lastname" value={username} onChange={e => { clearError(); setUsername(e.target.value); }} autoFocus />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="password-input" style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>Password</label>
                  <input id="password-input" className="form-input" type="password" placeholder="Enter your password" value={password} onChange={e => { clearError(); setPassword(e.target.value); }} onKeyDown={e => e.key === "Enter" && handlePasswordLogin()} />
                </div>
              </div>

              {error && <p style={{ color: "var(--danger)", fontSize: 13, marginBottom: 16 }}>{error}</p>}

              <button id="btn-password-submit" className="btn btn-primary btn-lg" style={{ width: "100%" }} onClick={handlePasswordLogin} disabled={loading || !username || !password}>
                {loading ? "Signing in…" : "Sign In"}
              </button>

              <p style={{ marginTop: 16, fontSize: 12.5, color: "var(--text-muted)", textAlign: "center" }}>
                Forgot your password? Ask your admin to reset it.
              </p>
            </>
          )}

        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>}>
      <LoginPageInner />
    </Suspense>
  );
}
