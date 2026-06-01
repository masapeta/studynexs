// API client — handles auth tokens and base URL
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const TENANT_SLUG =
  process.env.NEXT_PUBLIC_TENANT_SLUG || "test";

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

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export async function api<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Tenant-Slug": TENANT_SLUG,
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include", // For HttpOnly cookies
  });

  if (res.status === 401) {
    // The auth endpoints (refresh/login) returning 401 just means "no valid session
    // yet" — never refresh-and-redirect for those. Otherwise the public login page
    // reload-loops: auth-context calls /auth/refresh on mount, the 401 forces a
    // window.location redirect to "/", which remounts and calls /auth/refresh again.
    const isAuthCall = path.includes("/auth/");
    if (!isAuthCall) {
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
      if (typeof window !== "undefined" && window.location.pathname !== "/") {
        window.location.href = "/";
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
    throw new ApiError(res.status, text);
  }

  return res.json();
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshToken(): Promise<boolean> {
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
      headers: { "X-Tenant-Slug": TENANT_SLUG },
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
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return defaultMessage;
}

export const apiAuth = {
  sendOtp: (mobile: string) => api('/api/v1/auth/send-otp', { method: 'POST', body: JSON.stringify({ mobile }) }),
  verifyOtp: (mobile: string, otp: string) => api('/api/v1/auth/verify-otp', { method: 'POST', body: JSON.stringify({ mobile, otp }) }),
  loginPassword: (username: string, password: string) => api('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
};

