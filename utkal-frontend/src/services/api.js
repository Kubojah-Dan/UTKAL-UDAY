import axios from "axios";
import { AUTH_STORAGE_KEY } from "../context/AuthContext";

const rawBase =
  import.meta.env.VITE_API_BASE ||
  import.meta.env.VITE_ANDROID_API_BASE ||
  import.meta.env.OR ||
  "http://127.0.0.1:8000";

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
