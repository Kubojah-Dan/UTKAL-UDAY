import { api } from "./api";

export async function registerUser({ role, name, email, password, school, classGrade, studentId, teacherCode }) {
  const res = await api.post("/auth/register", {
    role,
    name,
    email: email.trim().toLowerCase(),
    password,
    school,
    class_grade: Number(classGrade),
    student_id: studentId || undefined,
    teacher_code: teacherCode || undefined,
  });
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
