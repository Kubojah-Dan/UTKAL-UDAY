import { api } from "./api";
import { getLocalQuestions, saveQuestionsLocally, db } from "../db/database";

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
  // Try local first
  const local = await db.questions.get(questionId);
  if (local) return local;

  // Fallback to API
  const res = await api.get(`/questions/${encodeURIComponent(questionId)}`);
  if (res.data) {
    await saveQuestionsLocally([res.data]);
  }
  return res.data;
}

export async function fetchQuestionList(params = {}) {
  // If offline, use local only
  if (!navigator.onLine) {
    return getLocalQuestions(params);
  }

  // Try API first to get fresh content if online
  try {
    const query = new URLSearchParams();
    if (params.limit) query.set("limit", String(params.limit));
    if (params.subject) query.set("subject", params.subject);
    if (params.grade) query.set("grade", String(params.grade));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    const res = await api.get(`/questions${suffix}`);

    if (res.data && Array.isArray(res.data)) {
      await saveQuestionsLocally(res.data);
    }
    return res.data;
  } catch (err) {
    console.warn("Fetch questions failed, falling back to local DB", err);
    return getLocalQuestions(params);
  }
}

export async function fetchModelReadiness() {
  const res = await api.get("/models/readiness");
  return res.data;
}
