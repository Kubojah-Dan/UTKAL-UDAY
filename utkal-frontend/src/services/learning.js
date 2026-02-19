import { api } from "./api";

export async function fetchRecommendations(studentId, params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.set("limit", String(params.limit));
  if (params.subject) query.set("subject", params.subject);
  if (params.grade) query.set("grade", String(params.grade));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const res = await api.get(`/recommend/${encodeURIComponent(studentId)}${suffix}`);
  return res.data;
}

export async function fetchQuestion(questionId) {
  const res = await api.get(`/questions/${encodeURIComponent(questionId)}`);
  return res.data;
}

export async function fetchQuestionList(params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.set("limit", String(params.limit));
  if (params.subject) query.set("subject", params.subject);
  if (params.grade) query.set("grade", String(params.grade));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const res = await api.get(`/questions${suffix}`);
  return res.data;
}

export async function fetchModelReadiness() {
  const res = await api.get("/models/readiness");
  return res.data;
}
