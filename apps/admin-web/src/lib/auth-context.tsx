"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, getAccessToken, getAccessTokenFromAuthResponse, setAccessToken } from "@/lib/api";
import { EMPTY_PERMISSIONS, UserPermissions } from "@/lib/permissions";

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
      try {
        const res = await api<Record<string, unknown>>("/api/v1/auth/refresh", {
          method: "POST",
        });
        const token = getAccessTokenFromAuthResponse(res);
        if (token) {
          setAccessToken(token);
        }
      } catch {
        // Refresh can fail cross-origin (localhost web → 127.0.0.1 API) while the
        // access token in sessionStorage is still valid — do not wipe it.
        if (!getAccessToken()) {
          setAccessToken(null);
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
