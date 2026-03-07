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

    const questions = res.data?.questions || res.data || [];
    if (Array.isArray(questions)) {
      await saveQuestionsLocally(questions);
    }
    return { questions, count: res.data?.count || questions.length };
  } catch (err) {
    console.warn("Fetch questions failed, falling back to local DB", err);
    const local = await getLocalQuestions(params);
    return { questions: local, count: local.length };
  }
}

export async function fetchModelReadiness() {
  const res = await api.get("/models/readiness");
  return res.data;
}
