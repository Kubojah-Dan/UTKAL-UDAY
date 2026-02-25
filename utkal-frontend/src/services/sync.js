import { api } from "./api";
import { saveBktParams, getQuest2Skill, saveQuest2Skill } from "./pouch";

export async function fetchQuest2SkillAndSave() {
  const res = await api.get("/quest2skill?limit=1000");
  if (res.status === 200) {
    await saveQuest2Skill(res.data);
    return res.data;
  }
  return null;
}

export async function fetchBktParamsAndSave() {
  const res = await api.get("/bkt/latest");
  if (res.status === 200) {
    await saveBktParams(res.data);
    return res.data;
  }
  return null;
}

export async function pushInteractions(studentId, interactions, apiKey) {
  const quest2skill = await getQuest2Skill().catch(() => null);
  const enriched = interactions.map((it) => {
    const mapping = quest2skill?.[String(it.quest_id)];
    return {
      interaction_id: it.interaction_id,
      quest_id: String(it.quest_id),
      problem_id: it.problem_id || it.problemId || String(it.quest_id),
      timestamp: it.timestamp || Date.now(),
      outcome: !!it.outcome,
      time_ms: it.time_ms || 0,
      hints: it.hints || 0,
      path_steps: it.path_steps || 0,
      steps_json: it.steps_json || "",
      skill_id: it.skill_id ?? (mapping ? String(mapping.skill_id) : null),
      subject: it.subject || null,
      grade: it.grade ?? null,
      school: it.school || null,
      class_grade: it.class_grade ?? null,
      xp_awarded: Number(it.xp_awarded || 0)
    };
  });

  const payload = { student_id: studentId, device_info: { app_version: "0.1.0" }, interactions: enriched };
  const headers = {};
  if (apiKey) headers["X-API-Key"] = apiKey;

  const resp = await api.post("/sync", payload, { headers });
  if (resp.status === 200) {
    if (resp.data?.bkt_params) {
      await saveBktParams(resp.data.bkt_params);
    }
    return resp.data;
  } else {
    throw new Error(`Sync failed ${resp.status}`);
  }
}
