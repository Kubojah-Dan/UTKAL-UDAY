import { api } from "./api";

export async function registerUser(payload) {
  // Ensure we send snake_case to backend
  const data = {
    role: payload.role,
    name: payload.name,
    email: payload.email.trim().toLowerCase(),
    password: payload.password,
    school: payload.school,
    district: payload.district,
    class_grade: Number(payload.class_grade || payload.classGrade),
    student_id: payload.student_id || payload.studentId || undefined,
    teacher_code: payload.teacher_code || payload.teacherCode || undefined,
  };
  const res = await api.post("/auth/register", data);
  return res.data;
}

export async function loginUser({ email, password }) {
  const res = await api.post("/auth/login", {
    email: email.trim().toLowerCase(),
    password,
  });
  return res.data;
}

export async function fetchMe() {
  const res = await api.get("/auth/me");
  return res.data;
}
