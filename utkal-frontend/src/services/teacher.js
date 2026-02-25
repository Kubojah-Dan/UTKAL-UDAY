import { api } from "./api";

export async function fetchTeacherAnalytics(params = {}) {
  const query = new URLSearchParams();
  if (params.school) query.set("school", params.school);
  if (params.classGrade) query.set("class_grade", String(params.classGrade));
  if (params.recentLimit) query.set("recent_limit", String(params.recentLimit));
  if (params.trendDays) query.set("trend_days", String(params.trendDays));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const res = await api.get(`/teacher/analytics${suffix}`);
  return res.data;
}

export async function fetchStudentDetail(studentId) {
  const res = await api.get(`/teacher/student/${encodeURIComponent(studentId)}`);
  return res.data;
}
