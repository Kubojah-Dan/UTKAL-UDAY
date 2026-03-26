import Dexie from "dexie";

export const db = new Dexie("UtkalUdayDB");

db.version(2).stores({
  questions: "id, subject, grade, topic, type",
  interactions: "id, quest_id, student_id, synced, timestamp",
  sync_queue: "++id, student_id, synced, created_at",
});

export const getLocalQuestions = async (params = {}) => {
  let collection = db.questions;
  if (params.subject) collection = collection.where("subject").equals(params.subject);
  if (params.grade) {
    const grade = Number(params.grade);
    if (params.subject) {
      collection = collection.filter((q) => q.grade === grade);
    } else {
      collection = collection.where("grade").equals(grade);
    }
  }
  return collection.toArray();
};

export const saveQuestionsLocally = async (questions) => {
  return db.questions.bulkPut(questions);
};

export const queueInteraction = async (interaction) => {
  return db.interactions.add({
    ...interaction,
    id: crypto.randomUUID(),
    synced: 0,
    timestamp: Date.now(),
  });
};

export const getUnsyncedInteractions = async () => {
  return db.interactions.where("synced").equals(0).toArray();
};

export const markInteractionsSynced = async (ids) => {
  return db.interactions.where("id").anyOf(ids).modify({ synced: 1 });
};

// Offline sync queue — never lose an interaction
export const addToSyncQueue = async (interaction) => {
  await db.interactions.add({
    ...interaction,
    id: crypto.randomUUID(),
    synced: 0,
    timestamp: Date.now(),
  });

  // Also add to sync_queue for retry tracking
  await db.sync_queue.add({
    student_id: interaction.student_id,
    payload: interaction,
    synced: 0,
    created_at: new Date().toISOString(),
  });

  if (navigator.onLine) {
    _flushSyncQueue().catch(() => null);
  }
};

async function _flushSyncQueue() {
  const pending = await db.sync_queue.where("synced").equals(0).toArray();
  if (!pending.length) return;

  const { api } = await import("../services/api");
  for (const item of pending) {
    try {
      await api.post("/sync", {
        student_id: item.student_id,
        interactions: [item.payload],
      });
      await db.sync_queue.update(item.id, { synced: 1 });
    } catch (_) {
      // Will retry on next online event
    }
  }
}

// Auto-flush when coming back online
if (typeof window !== "undefined") {
  window.addEventListener("online", () => _flushSyncQueue().catch(() => null));
}
