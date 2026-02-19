import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "utkal_auth_session";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        setSession(JSON.parse(raw));
      }
    } catch (err) {
      console.warn("Could not restore auth session", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = (nextSession) => {
    setSession(nextSession);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
  };

  const logout = () => {
    setSession(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  const value = useMemo(
    () => ({
      loading,
      session,
      token: session?.token || null,
      user: session?.user || null,
      login,
      logout,
      isStudent: session?.user?.role === "student",
      isTeacher: session?.user?.role === "teacher",
    }),
    [loading, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}

export const AUTH_STORAGE_KEY = STORAGE_KEY;
