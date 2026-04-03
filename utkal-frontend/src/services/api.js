import axios from "axios";
import { AUTH_STORAGE_KEY } from "../context/AuthContext";

function isCapacitorShell() {
  if (typeof window === "undefined") return false;
  const { hostname, origin, port, protocol } = window.location;
  return protocol === "capacitor:" || (origin === "http://localhost" && hostname === "localhost" && port === "");
}

const rawBase = isCapacitorShell()
  ? (
      import.meta.env.VITE_ANDROID_API_BASE ||
      import.meta.env.VITE_API_BASE ||
      "http://10.0.2.2:8000"
    )
  : (
      import.meta.env.VITE_API_BASE ||
      import.meta.env.VITE_ANDROID_API_BASE ||
      "http://127.0.0.1:8000"
    );

const BASE = rawBase.replace(/\/+$/, "");
export const API_BASE = BASE;

export const api = axios.create({
  baseURL: BASE,
  timeout: 60000,  // 60 seconds for document upload
  headers: { "Content-Type": "application/json" }
});

api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return config;
    const session = JSON.parse(raw);
    if (session?.token) {
      config.headers.Authorization = `Bearer ${session.token}`;
    }
  } catch (err) {
    console.warn("Failed to attach auth token", err);
  }
  return config;
});
