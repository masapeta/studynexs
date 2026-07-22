// API client — handles auth tokens and base URL
// Use 127.0.0.1 (not localhost): on Windows, localhost often resolves to ::1 and can
// hit Docker/WSL on :8000 instead of the local uvicorn with edge-tts.
import { getTenantSlug } from "@/lib/tenant";
import {
  CUSTOMER_NETWORK_ERROR,
  CUSTOMER_SERVER_ERROR,
  sanitizeCustomerErrorMessage,
} from "@/lib/customer-errors";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
export { getTenantSlug, TENANT_SLUG } from "@/lib/tenant";

const PUBLIC_API_PATHS = [
  "/api/v1/tutor/tts/status",
  "/api/v1/demo/sessions",
  "/health",
  "/ready",
];

function isPublicApiPath(path: string): boolean {
  const bare = path.split("?")[0];
  if (PUBLIC_API_PATHS.some((p) => bare === p || bare.startsWith(p))) return true;
  if (bare.startsWith("/api/v1/demo/sessions/")) return true;
  return false;
}

/** Auth endpoints return flat JSON; domain endpoints use { data: ... }. */
export function getAccessTokenFromAuthResponse(
  body: Record<string, unknown>
): string | null {
  if (typeof body.access_token === "string") {
    return body.access_token;
  }
  const wrapped = body.data as Record<string, unknown> | undefined;
  if (wrapped && typeof wrapped.access_token === "string") {
    return wrapped.access_token;
  }
  return null;
}

const TOKEN_KEY = "sn_access_token";

function readStoredToken(): string | null {
  if (typeof sessionStorage === "undefined") return null;
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

let accessToken: string | null = readStoredToken();

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (typeof sessionStorage !== "undefined") {
    try {
      if (token) sessionStorage.setItem(TOKEN_KEY, token);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // Private mode / disabled storage — in-memory token still works for this tab.
    }
  }
}

export function getAccessToken() {
  return accessToken;
}

// Callers should pass an explicit `T`; default stays loose for legacy pages.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function api<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers: Record<string, string> = {
    "X-Tenant-Slug": getTenantSlug(),
    ...(options.headers as Record<string, string>),
  };
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (accessToken && !isPublicApiPath(path)) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      credentials: "include", // For HttpOnly cookies
    });
  } catch {
    throw new ApiError(0, CUSTOMER_NETWORK_ERROR);
  }

  if (res.status === 401) {
    // The auth endpoints (refresh/login) returning 401 just means "no valid session
    // yet" — never refresh-and-redirect for those. Otherwise the public login page
    // reload-loops: auth-context calls /auth/refresh on mount, the 401 forces a
    // window.location redirect to "/", which remounts and calls /auth/refresh again.
    const isAuthCall = path.includes("/auth/");
    if (!isAuthCall && !isPublicApiPath(path)) {
      const refreshed = await refreshToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${accessToken}`;
        const retry = await fetch(`${API_URL}${path}`, {
          ...options,
          headers,
          credentials: "include",
        });
        if (!retry.ok) throw new ApiError(retry.status, await retry.text());
        return retry.json();
      }
      // Session truly gone — bounce to login, but only if we aren't already there.
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    throw new ApiError(401, "Unauthorized");
  }

  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After");
    const suffix = retryAfter ? ` Try again in ${retryAfter} seconds.` : "";
    throw new ApiError(429, `Too many requests.${suffix}`);
  }

  if (!res.ok) {
    let text = await res.text();
    try {
      const json = JSON.parse(text);
      if (json.detail) text = json.detail;
    } catch {}
    const safe = sanitizeCustomerErrorMessage(
      typeof text === "string" ? text : String(text),
      res.status,
      CUSTOMER_SERVER_ERROR
    );
    throw new ApiError(res.status, safe);
  }

  return res.json();
}

let refreshInFlight: Promise<boolean> | null = null;

export async function refreshToken(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = doRefreshToken().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

async function doRefreshToken(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "X-Tenant-Slug": getTenantSlug() },
    });
    if (res.ok) {
      const data = await res.json();
      accessToken = getAccessTokenFromAuthResponse(data);
      return !!accessToken;
    }
    return false;
  } catch {
    return false;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getApiErrorMessage(error: unknown, defaultMessage: string): string {
  if (error instanceof ApiError) {
    return sanitizeCustomerErrorMessage(error.message, error.status, defaultMessage);
  }
  if (error instanceof Error) {
    return sanitizeCustomerErrorMessage(error.message, 0, defaultMessage);
  }
  return defaultMessage;
}

/** Fetch a protected PDF/HTML document; returns a blob URL for in-app preview (caller must revoke). */
const _fetchDocInFlight = new Map<string, Promise<string>>();

export async function fetchProtectedDocumentUrl(path: string): Promise<string> {
  const inflight = _fetchDocInFlight.get(path);
  if (inflight) return inflight;

  const promise = (async () => {
    const res = await fetch(`${API_URL}${path}`, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
        "X-Tenant-Slug": getTenantSlug(),
      },
      credentials: "include",
    });

    if (!res.ok) {
      let message = "Could not open this document. Please try again.";
      try {
        const body = await res.json();
        if (typeof body.detail === "string") {
          message = sanitizeCustomerErrorMessage(body.detail, res.status, message);
        }
      } catch {
        const text = await res.text().catch(() => "");
        if (text) {
          message = sanitizeCustomerErrorMessage(text.slice(0, 200), res.status, message);
        }
      }
      throw new ApiError(res.status, message);
    }

    const rawType = res.headers.get("content-type") || "";
    const contentType = rawType.split(";")[0].trim();
    const buffer = await res.arrayBuffer();
    const mime =
      contentType === "text/html"
        ? "text/html;charset=utf-8"
        : contentType || "application/octet-stream";
    return URL.createObjectURL(new Blob([buffer], { type: mime }));
  })().finally(() => {
    _fetchDocInFlight.delete(path);
  });

  _fetchDocInFlight.set(path, promise);
  return promise;
}

/** Public TTS capability probe — no auth, no 401 redirect. */
export type TutorTtsStatus = {
  enabled: boolean;
  voice: string;
  voice_display: string;
  backend: string;
};

export async function fetchTtsStatus(): Promise<TutorTtsStatus> {
  const res = await fetch(`${API_URL}/api/v1/tutor/tts/status`, {
    headers: { "X-Tenant-Slug": getTenantSlug() },
    credentials: "include",
  });
  if (!res.ok) {
    throw new ApiError(res.status, "Could not check Neerja voice status.");
  }
  const json = (await res.json()) as { data?: TutorTtsStatus };
  const data = json.data;
  if (!data) {
    throw new ApiError(502, "Invalid TTS status response from API.");
  }
  return data;
}

/** POST JSON → binary audio (tutor TTS). Retries once after token refresh on 401. */
export type TutorSpeechResult = {
  blob: Blob;
  voice: string;
  voiceDisplay: string;
  backend: string;
};

export async function fetchTutorSpeechBlob(
  text: string,
  voice: string,
  stepTitle?: string
): Promise<TutorSpeechResult> {
  const body = JSON.stringify({
    text,
    voice,
    ...(stepTitle ? { step_title: stepTitle } : {}),
  });
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAccessToken()}`,
    "X-Tenant-Slug": getTenantSlug(),
  };

  let res = await fetch(`${API_URL}/api/v1/tutor/tts`, {
    method: "POST",
    headers,
    body,
    credentials: "include",
  });

  if (res.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      res = await fetch(`${API_URL}/api/v1/tutor/tts`, {
        method: "POST",
        headers: {
          ...headers,
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body,
        credentials: "include",
      });
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, "Teacher voice is temporarily unavailable.");
  }

  const blob = await res.blob();
  if (!blob.size) {
    throw new ApiError(502, "Teacher voice returned empty audio.");
  }
  return {
    blob,
    voice: res.headers.get("X-TTS-Voice") || voice,
    voiceDisplay: res.headers.get("X-TTS-Voice-Display") || "Neerja",
    backend: res.headers.get("X-TTS-Backend") || "edge",
  };
}

export const apiAuth = {
  sendOtp: (mobile: string) => api('/api/v1/auth/send-otp', { method: 'POST', body: JSON.stringify({ mobile }) }),
  verifyOtp: (mobile: string, otp: string) => api('/api/v1/auth/verify-otp', { method: 'POST', body: JSON.stringify({ mobile, otp }) }),
  loginPassword: (username: string, password: string) => api('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
};

