import Dexie from "dexie";

export const db = new Dexie("UtkalUdayDB");

// v1 → baseline
// v2 → sync_queue added
// v3 → richer sync_queue (action_type, retry_count, status), study_cards table
db.version(3).stores({
  questions:    "id, subject, grade, topic, type",
  interactions: "id, quest_id, student_id, synced, timestamp",
  sync_queue:   "++id, student_id, action_type, synced, status, created_at, retry_count",
  study_cards:  "id, subject, grade, chapter, synced",
});

// ── Action type constants ──────────────────────────────────────────────────
export const ACTION_TYPES = {
  ANSWER_SUBMITTED: "answer_submitted",
  XP_EARNED:        "xp_earned",
  BADGE_UNLOCKED:   "badge_unlocked",
  STREAK_UPDATED:   "streak_updated",
};

// ── Status constants ───────────────────────────────────────────────────────
export const SYNC_STATUS = {
  PENDING: "pending",
  SYNCING: "syncing",
  SYNCED:  "synced",
  FAILED:  "failed",   // max retries exhausted — never silently discarded
};

const MAX_RETRY = 10;

// ── Questions ──────────────────────────────────────────────────────────────
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

// ── Interactions (PouchDB-compatible layer) ────────────────────────────────
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

// ── Study Cards ────────────────────────────────────────────────────────────
export const saveStudyCardsLocally = async (cards) => {
  return db.study_cards.bulkPut(cards);
};

export const getLocalStudyCards = async ({ subject, grade, chapter } = {}) => {
  let col = db.study_cards;
  if (subject) col = col.where("subject").equals(subject);
  return col.toArray().then((cards) => {
    let result = cards;
    if (grade) result = result.filter((c) => c.grade === Number(grade));
    if (chapter) result = result.filter((c) => c.chapter === chapter);
    return result;
  });
};

// ── Sync Queue — never lose an interaction ─────────────────────────────────
/**
 * Add an action to the sync queue.
 * @param {Object} opts
 * @param {string} opts.student_id
 * @param {string} opts.action_type  - one of ACTION_TYPES
 * @param {Object} opts.payload      - the full interaction/event payload
 * @param {string} [opts.conflict_resolution] - 'higher_wins' (default) | 'last_write_wins'
 */
export const addToSyncQueue = async ({
  student_id,
  action_type = ACTION_TYPES.ANSWER_SUBMITTED,
  payload,
  conflict_resolution = "higher_wins",
}) => {
  // Always persist to interactions table first (belt-and-suspenders)
  await db.interactions.add({
    ...payload,
    id: crypto.randomUUID(),
    synced: 0,
    timestamp: Date.now(),
  });

  // Also enqueue in sync_queue for robust retry tracking
  await db.sync_queue.add({
    student_id,
    action_type,
    payload,
    conflict_resolution,
    status:      SYNC_STATUS.PENDING,
    synced:      0,
    retry_count: 0,
    created_at:  new Date().toISOString(),
  });

  if (navigator.onLine) {
    _flushSyncQueue().catch(() => null);
  }
};

/**
 * Flush pending sync_queue items in chronological order.
 * Marks synced:1 / status:'synced' ONLY after server confirmation.
 * Increments retry_count on failure; marks status:'failed' after MAX_RETRY.
 * Never silently discards records.
 */
export async function _flushSyncQueue() {
  // Drain in chronological order (lowest id first since it's auto-incremented)
  const pending = await db.sync_queue
    .where("status")
    .equals(SYNC_STATUS.PENDING)
    .sortBy("id");

  if (!pending.length) return;

  const { api } = await import("../services/api");

  for (const item of pending) {
    // Mark as syncing so concurrent flush attempts skip it
    await db.sync_queue.update(item.id, { status: SYNC_STATUS.SYNCING });

    try {
      const res = await api.post("/sync", {
        student_id:  item.student_id,
        action_type: item.action_type,
        interactions: [item.payload],
      });

      if (res.status === 200 || res.status === 201) {
        await db.sync_queue.update(item.id, {
          synced: 1,
          status: SYNC_STATUS.SYNCED,
        });
      } else if (res.status === 409) {
        // Conflict — apply resolution strategy, then re-queue as pending
        const { resolveConflict } = await import("../services/conflictResolver");
        const resolved = resolveConflict(item.payload, res.data?.server_value, item.conflict_resolution);
        await db.sync_queue.update(item.id, {
          payload: resolved,
          status:  SYNC_STATUS.PENDING,
          retry_count: item.retry_count + 1,
        });
      } else {
        throw new Error(`Unexpected status ${res.status}`);
      }
    } catch (err) {
      const newRetry = (item.retry_count || 0) + 1;
      const newStatus = newRetry >= MAX_RETRY ? SYNC_STATUS.FAILED : SYNC_STATUS.PENDING;
      await db.sync_queue.update(item.id, {
        status:      newStatus,
        retry_count: newRetry,
        last_error:  String(err?.message || err),
      });
    }
  }
}

/** Count pending (unsynced + non-failed) items — used by connectivity UI */
export async function getPendingSyncCount() {
  return db.sync_queue.where("status").equals(SYNC_STATUS.PENDING).count();
}

/** Count failed items — so they are visible to users, never lost */
export async function getFailedSyncCount() {
  return db.sync_queue.where("status").equals(SYNC_STATUS.FAILED).count();
}

// Auto-flush when coming back online
if (typeof window !== "undefined") {
  window.addEventListener("online", () => _flushSyncQueue().catch(() => null));
}
