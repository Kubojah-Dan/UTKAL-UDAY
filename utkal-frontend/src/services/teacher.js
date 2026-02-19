import { api } from "./api";

export async function fetchTeacherAnalytics() {
  const res = await api.get("/teacher/analytics");
  return res.data;
}

export async function fetchStudentDetail(studentId) {
  const res = await api.get(`/teacher/student/${encodeURIComponent(studentId)}`);
  return res.data;
}
