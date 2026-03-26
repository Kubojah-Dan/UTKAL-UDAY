import { getPendingInteractions, markInteractionsSynced } from "./events";
import { pushInteractions } from "./sync";
import { db } from "../db/database";

export async function flushPendingInteractions() {
  if (!navigator.onLine) return false;

  // Flush main interactions table
  const interactions = await getPendingInteractions(5000);
  if (interactions && interactions.length > 0) {
    try {
      const grouped = {};
      interactions.forEach((it) => {
        const sid = it.student_id || "anonymous";
        grouped[sid] = grouped[sid] || { docs: [], payload: [] };
        grouped[sid].docs.push(it._id);
        grouped[sid].payload.push({
          interaction_id: it.interaction_id,
          quest_id: it.quest_id,
          problem_id: it.problem_id || it.problemId || it.quest_id,
          timestamp: it.timestamp,
          outcome: it.outcome,
          time_ms: it.time_ms,
          hints: it.hints,
          path_steps: it.path_steps,
          steps_json: it.steps_json,
          skill_id: it.skill_id,
          subject: it.subject,
          grade: it.grade,
          school: it.school,
          class_grade: it.class_grade,
          xp_awarded: Number(it.xp_awarded || 0),
        });
      });

      for (const [sid, group] of Object.entries(grouped)) {
        await pushInteractions(sid, group.payload);
        await markInteractionsSynced(group.docs);
      }
    } catch (e) {
      console.warn("Flush interactions failed", e);
    }
  }

  // Flush sync_queue (belt-and-suspenders for offline-queued items)
  try {
    const pending = await db.sync_queue.where("synced").equals(0).toArray();
    if (pending.length > 0) {
      const { api } = await import("./api");
      for (const item of pending) {
        try {
          await api.post("/sync", {
            student_id: item.student_id,
            interactions: [item.payload],
          });
          await db.sync_queue.update(item.id, { synced: 1 });
        } catch (_) {}
      }
    }
  } catch (e) {
    console.warn("Flush sync_queue failed", e);
  }

  return true;
}

export function startAutoFlush(intervalMs = 60 * 1000) {
  const run = () => flushPendingInteractions().catch(console.error);
  const intervalId = setInterval(run, intervalMs);

  window.addEventListener("online", run);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") run();
  });

  run();

  return () => {
    clearInterval(intervalId);
    window.removeEventListener("online", run);
  };
}
