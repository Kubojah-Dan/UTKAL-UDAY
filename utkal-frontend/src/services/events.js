import { db } from "./pouch";
import { v4 as uuidv4 } from "uuid";

/**
 * Interaction doc shape:
 * {
 *   _id: "interaction:<uuid>",
 *   type: "interaction",
 *   student_id: "...",
 *   quest_id: "988",
 *   problemId: "104051118",
 *   skill_id: 1,
 *   timestamp: 1670000000,
 *   outcome: true,
 *   time_ms: 4500,
 *   hints: 1,
 *   path_steps: 3,
 *   steps_json: []
 * }
 */

export async function addInteraction(interaction) {
  const interactionId = interaction.interaction_id || uuidv4();
  const id = "interaction:" + interactionId;
  const doc = {
    _id: id,
    type: "interaction",
    interaction_id: interactionId,
    synced: false,
    created_at: Date.now(),
    ...interaction
  };

  try {
    return await db.put(doc);
  } catch (e) {
    if (e.status === 409) {
      const existing = await db.get(id);
      return db.put({ ...existing, ...doc });
    }
    throw e;
  }
}

export async function bulkAddInteractions(interactions) {
  const docs = interactions.map((it) => {
    const interactionId = it.interaction_id || uuidv4();
    return {
      _id: "interaction:" + interactionId,
      type: "interaction",
      interaction_id: interactionId,
      synced: false,
      created_at: Date.now(),
      ...it
    };
  });
  return db.bulkDocs(docs);
}

export async function getAllInteractions(limit = 1000) {
  try {
    const res = await db.allDocs({ include_docs: true });
    const docs = res.rows
      .map((r) => r.doc)
      .filter((d) => d.type === "interaction")
      .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
    return docs.slice(0, limit);
  } catch (e) {
    console.error("getAllInteractions error", e);
    return [];
  }
}

export async function getPendingInteractions(limit = 1000) {
  const all = await getAllInteractions(10000);
  return all.filter((d) => !d.synced).slice(0, limit);
}

export async function markInteractionsSynced(docIds = []) {
  if (!docIds.length) return;
  const res = await db.allDocs({ include_docs: true, keys: docIds });
  const updates = res.rows
    .map((r) => r.doc)
    .filter(Boolean)
    .map((doc) => ({
      ...doc,
      synced: true,
      synced_at: Date.now()
    }));
  if (updates.length) {
    await db.bulkDocs(updates);
  }
}

export async function getInteractionsByStudent(studentId) {
  const all = await getAllInteractions(5000);
  return all.filter((d) => String(d.student_id) === String(studentId));
}

export async function computeInteractionStats(studentId = null) {
  const all = studentId ? await getInteractionsByStudent(studentId) : await getAllInteractions(5000);
  const total = all.length;
  const correct = all.filter((d) => d.outcome).length;
  const avgTime = all.reduce((s, x) => s + (x.time_ms || 0), 0) / Math.max(1, total);
  const perSkill = {};
  const perSubject = {};
  all.forEach((d) => {
    const s = String(d.skill_id || "unknown");
    const subject = String(d.subject || "Unknown");
    perSkill[s] = perSkill[s] || { attempts: 0, correct: 0 };
    perSkill[s].attempts += 1;
    if (d.outcome) perSkill[s].correct += 1;

    perSubject[subject] = perSubject[subject] || { attempts: 0, correct: 0 };
    perSubject[subject].attempts += 1;
    if (d.outcome) perSubject[subject].correct += 1;
  });
  return { total, correct, accuracy: (correct / Math.max(1, total)), avgTime, perSkill, perSubject };
}
