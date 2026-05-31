"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, getAccessTokenFromAuthResponse, setAccessToken } from "@/lib/api";

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
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  loginWithTokens: (tokens: { access_token: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  loginWithTokens: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

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
          const profile = await api<{ data: User }>("/api/v1/users/me");
          setUser(profile.data);
        }
      } catch {
        setAccessToken(null);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const loginWithTokens = async (tokens: { access_token: string }) => {
    setAccessToken(tokens.access_token);
    const profile = await api<{ data: User }>("/api/v1/users/me");
    setUser(profile.data);
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
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithTokens, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
