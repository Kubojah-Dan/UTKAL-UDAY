import { useState, useEffect, useCallback } from "react";
import { getPendingSyncCount, getFailedSyncCount } from "../db/database";

/**
 * Returns live online/offline status.
 * Reacts to both the navigator.onLine flag and network events.
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline  = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online",  handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online",  handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return isOnline;
}

/**
 * Returns the count of pending (unsynced) and failed items in sync_queue.
 * Polls every 10s and also refreshes on online/offline transitions.
 */
export function useSyncQueueStatus() {
  const [pendingCount, setPendingCount] = useState(0);
  const [failedCount,  setFailedCount]  = useState(0);
  const [isSyncing,    setIsSyncing]    = useState(false);
  const isOnline = useOnlineStatus();

  const refresh = useCallback(async () => {
    try {
      const [pending, failed] = await Promise.all([
        getPendingSyncCount(),
        getFailedSyncCount(),
      ]);
      setPendingCount(pending);
      setFailedCount(failed);
    } catch (_) {
      // DB may not be initialized yet — silently ignore
    }
  }, []);

  // Poll every 10 seconds
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10_000);
    return () => clearInterval(id);
  }, [refresh]);

  // Also refresh on connectivity change
  useEffect(() => {
    refresh();
  }, [isOnline, refresh]);

  const manualSync = useCallback(async () => {
    if (!isOnline || isSyncing) return;
    setIsSyncing(true);
    try {
      const { flushPendingInteractions } = await import("../services/offlineSync");
      await flushPendingInteractions();
      await refresh();
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, isSyncing, refresh]);

  return { pendingCount, failedCount, isOnline, isSyncing, manualSync, refresh };
}
