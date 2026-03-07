import { api } from "./api";
import { saveBktParams } from "./pouch";
import { getPendingInteractions, markInteractionsSynced as markPouchSynced } from "./events";

export async function pushInteractions(studentId, interactions, apiKey) {
  const res = await api.post("/sync", {
    student_id: studentId,
    interactions: interactions
  }, {
    headers: apiKey ? { "x-api-key": apiKey } : {}
  });
  return res.data;
}

export async function fetchBktParamsAndSave() {
  const res = await api.get("/bkt/latest");
  if (res.data) {
    await saveBktParams(res.data);
  }
  return res.data;
}

let isSyncing = false;

export const syncData = async (studentId) => {
  if (isSyncing || !navigator.onLine) {
    console.log('Sync skipped:', { isSyncing, online: navigator.onLine });
    return;
  }

  isSyncing = true;
  try {
    const unsynced = await getPendingInteractions();
    console.log(`Found ${unsynced.length} unsynced interactions`);
    
    if (unsynced.length === 0) return;

    console.log(`Syncing ${unsynced.length} interactions...`);

    // We send them in one batch to the sync endpoint
    const payload = {
      student_id: studentId,
      interactions: unsynced.map(({ _id, _rev, id, synced, type, created_at, ...rest }) => rest),
      device_info: {
        platform: navigator.platform,
        userAgent: navigator.userAgent,
        offline_sync: true
      }
    };

    const res = await api.post("/sync", payload);
    console.log('Sync response:', res.data);

    if (res.status === 200 || res.status === 201) {
      const ids = unsynced.map(u => u._id);
      await markPouchSynced(ids);
      console.log("Sync successful, marked", ids.length, "interactions as synced");
    }
  } catch (err) {
    console.error("Sync failed:", err.response?.data || err.message);
  } finally {
    isSyncing = false;
  }
};

export const initBackgroundSync = (studentId) => {
  if (!studentId) return;

  window.addEventListener("online", () => {
    console.log("Device online, triggering sync...");
    syncData(studentId);
  });

  // Also try sync on init if online
  if (navigator.onLine) {
    syncData(studentId);
  }
};
