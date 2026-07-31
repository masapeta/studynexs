"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, getAccessToken, getAccessTokenFromAuthResponse, setAccessToken } from "@/lib/api";
import { EMPTY_PERMISSIONS, UserPermissions } from "@/lib/permissions";
import { clearProspectTenantSlug, setDemoSessionToken } from "@/lib/tenant";

interface User {
  id: string;
  full_name: string;
  email: string | null;
  role: string;
  school_id: string;
  profile_photo: string | null;
}

interface AuthState {
  user: User | null;
  permissions: UserPermissions | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  loginWithTokens: (tokens: { access_token: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  permissions: null,
  loading: true,
  login: async () => {},
  loginWithTokens: async () => {},
  logout: async () => {},
});

// Non-sensitive hint that a session may exist. The refresh token is an
// HttpOnly cookie invisible to JS, so without this flag every anonymous
// visit would POST /auth/refresh, guaranteeing 401 noise and consuming
// auth rate-limit budget for nothing.
const SESSION_HINT_KEY = "sn_has_session";

function hasSessionHint(): boolean {
  try {
    return typeof localStorage !== "undefined" && localStorage.getItem(SESSION_HINT_KEY) === "1";
  } catch {
    return false;
  }
}

function setSessionHint(on: boolean) {
  try {
    if (typeof localStorage === "undefined") return;
    if (on) localStorage.setItem(SESSION_HINT_KEY, "1");
    else localStorage.removeItem(SESSION_HINT_KEY);
  } catch {
    // Storage unavailable (private mode) — refresh-on-mount stays as fallback.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<UserPermissions | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadProfile() {
    const [profile, permsRes] = await Promise.all([
      api<{ data: User }>("/api/v1/users/me"),
      api<{ data: UserPermissions }>("/api/v1/users/me/permissions").catch(() => null),
    ]);
    setUser(profile.data);
    setPermissions(permsRes?.data ?? EMPTY_PERMISSIONS);
  }

  // Try to restore session on mount
  useEffect(() => {
    async function init() {
      // Only attempt a refresh when a prior session plausibly exists —
      // anonymous visitors skip the guaranteed-401 round trip entirely.
      if (hasSessionHint() || getAccessToken()) {
        try {
          const res = await api<Record<string, unknown>>("/api/v1/auth/refresh", {
            method: "POST",
          });
          const token = getAccessTokenFromAuthResponse(res);
          if (token) {
            setAccessToken(token);
            setSessionHint(true);
          }
        } catch {
          // Refresh can fail cross-origin (localhost web → 127.0.0.1 API) while the
          // access token in sessionStorage is still valid — do not wipe it.
          if (!getAccessToken()) {
            setAccessToken(null);
            setSessionHint(false);
          }
        }
      }

      if (getAccessToken()) {
        try {
          await loadProfile();
        } catch {
          setAccessToken(null);
          setUser(null);
          setPermissions(null);
        }
      }

      setLoading(false);
    }
    init();
  }, []);

  const loginWithTokens = async (tokens: { access_token: string }) => {
    setAccessToken(tokens.access_token);
    setSessionHint(true);
    await loadProfile();
  };

  const login = async (username: string, password: string) => {
    const res = await api<Record<string, unknown>>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    const token = getAccessTokenFromAuthResponse(res);
    if (!token) {
      throw new Error("Login response did not include an access token");
    }
    await loginWithTokens({ access_token: token });
  };

  const logout = async () => {
    try {
      await api("/api/v1/auth/logout", { method: "POST" });
    } catch {}
    setAccessToken(null);
    setSessionHint(false);
    clearProspectTenantSlug();
    setDemoSessionToken(null);
    setUser(null);
    setPermissions(null);
  };

  return (
    <AuthContext.Provider value={{ user, permissions, loading, login, loginWithTokens, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
