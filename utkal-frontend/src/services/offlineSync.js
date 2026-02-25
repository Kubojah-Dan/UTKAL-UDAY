import { getPendingInteractions, markInteractionsSynced } from "./events";
import { pushInteractions } from "./sync";

// naive dispatcher: collect unsent interactions and push to server
export async function flushPendingInteractions(apiKey) {
    if (!navigator.onLine) return false;
    const interactions = await getPendingInteractions(5000);
    if (!interactions || interactions.length === 0) return true;
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
                xp_awarded: Number(it.xp_awarded || 0)
            });
        });

        for (const [sid, group] of Object.entries(grouped)) {
            await pushInteractions(sid, group.payload, apiKey);
            await markInteractionsSynced(group.docs);
        }
        console.log("Flushed interactions successfully");
        return true;
    } catch (e) {
        console.warn("Flush failed", e);
        return false;
    }
}

// start a periodic flush (call this once on app start)
export function startAutoFlush(apiKey, intervalMs = 60 * 1000) {
    const run = () => flushPendingInteractions(apiKey).catch(console.error);
    const intervalId = setInterval(run, intervalMs);
    const onlineListener = () => run();
    const visibleListener = () => {
        if (document.visibilityState === "visible") run();
    };

    window.addEventListener("online", onlineListener);
    document.addEventListener("visibilitychange", visibleListener);

    run();

    return () => {
        clearInterval(intervalId);
        window.removeEventListener("online", onlineListener);
        document.removeEventListener("visibilitychange", visibleListener);
    };
}
