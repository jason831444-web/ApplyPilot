"use client";

import { createContext, createElement, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { apiRequest } from "@/lib/api";
import {
  clearStoredToken,
  clearStoredUserJson,
  getStoredToken,
  getStoredUserJson,
  setStoredToken,
  setStoredUserJson,
} from "@/lib/auth";
import type { TokenResponse, User } from "@/lib/types";

type LoginPayload = {
  email: string;
  password: string;
};

type RegisterPayload = LoginPayload & {
  full_name: string;
};

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = getStoredToken();
    const storedUserJson = getStoredUserJson();
    setToken(storedToken);

    if (storedUserJson) {
      try {
        setUser(JSON.parse(storedUserJson) as User);
      } catch {
        clearStoredUserJson();
      }
    }

    setIsLoading(false);
  }, []);

  async function login(payload: LoginPayload) {
    const response = await apiRequest<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: payload,
    });
    setStoredToken(response.access_token);
    setStoredUserJson(JSON.stringify(response.user));
    setToken(response.access_token);
    setUser(response.user);
  }

  async function register(payload: RegisterPayload) {
    await apiRequest<User>("/api/auth/register", {
      method: "POST",
      body: payload,
    });
    await login({ email: payload.email, password: payload.password });
  }

  function logout() {
    clearStoredToken();
    clearStoredUserJson();
    setToken(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      isLoading,
      login,
      register,
      logout,
    }),
    [token, user, isLoading],
  );

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
