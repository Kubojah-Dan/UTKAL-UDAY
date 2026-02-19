import { api } from "./api";

export async function loginUser({ role, name, studentId, password }) {
  const payload = {
    role,
    name,
    student_id: studentId || undefined,
    password: password || undefined,
  };
  const res = await api.post("/auth/login", payload);
  return res.data;
}

export async function fetchMe() {
  const res = await api.get("/auth/me");
  return res.data;
}
