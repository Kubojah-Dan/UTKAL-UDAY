import React, { useEffect, useState } from "react";
import { RefreshCw, WifiOff, AlertCircle } from "lucide-react";
import { useSyncQueueStatus } from "../hooks/useSyncStatus";

/**
 * Slim banner that appears below the header when there are pending sync items.
 * Auto-dismisses when pendingCount reaches 0.
 * Never blocks interaction — thin strip with a retry button.
 */
export default function SyncStatusBanner() {
  const { pendingCount, failedCount, isOnline, isSyncing, manualSync } = useSyncQueueStatus();
  const [dismissed, setDismissed] = useState(false);

  // Auto-dismiss when everything is synced
  useEffect(() => {
    if (pendingCount === 0 && failedCount === 0) {
      setDismissed(true);
    } else {
      setDismissed(false);
    }
  }, [pendingCount, failedCount]);

  // Nothing to show
  if (dismissed || (pendingCount === 0 && failedCount === 0)) return null;

  const hasFailed = failedCount > 0;

  return (
    <div
      className="sync-status-banner"
      data-status={hasFailed ? "failed" : isOnline ? "syncing" : "offline"}
      role="status"
      aria-live="polite"
    >
      <div className="sync-banner-inner">
        <span className="sync-banner-icon">
          {hasFailed ? (
            <AlertCircle size={15} />
          ) : !isOnline ? (
            <WifiOff size={15} />
          ) : (
            <RefreshCw size={15} className={isSyncing ? "spinning" : ""} />
          )}
        </span>

        <span className="sync-banner-text">
          {hasFailed && `${failedCount} item${failedCount !== 1 ? "s" : ""} failed to sync — `}
          {!isOnline
            ? `Offline — ${pendingCount} answer${pendingCount !== 1 ? "s" : ""} pending sync`
            : `${pendingCount} answer${pendingCount !== 1 ? "s" : ""} pending sync`}
        </span>

        {isOnline && !isSyncing && (
          <button
            className="sync-banner-retry"
            onClick={manualSync}
            aria-label="Retry sync now"
          >
            Sync now
          </button>
        )}

        {isSyncing && (
          <span className="sync-banner-syncing">Syncing…</span>
        )}

        <button
          className="sync-banner-dismiss"
          onClick={() => setDismissed(true)}
          aria-label="Dismiss sync notification"
        >
          ×
        </button>
      </div>
    </div>
  );
}
