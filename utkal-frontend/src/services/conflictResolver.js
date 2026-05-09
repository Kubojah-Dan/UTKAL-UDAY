/**
 * Conflict resolution strategies for offline sync.
 *
 * When two devices modify the same student data offline, we need a consistent
 * rule. For a student platform: students should NEVER lose progress they earned.
 *
 * Supported strategies:
 *  - 'higher_wins'     : Always keep the higher XP/accuracy value (default)
 *  - 'last_write_wins' : Timestamp-based; most recent update wins
 */

/**
 * Resolve a conflict between a local payload and a server value.
 *
 * @param {Object} local    - The locally queued interaction payload
 * @param {Object} server   - The server's current value for the same record
 * @param {string} strategy - 'higher_wins' | 'last_write_wins'
 * @returns {Object}        - The resolved payload to re-queue for sync
 */
export function resolveConflict(local, server, strategy = "higher_wins") {
  if (!server) return local;
  if (!local)  return server;

  if (strategy === "higher_wins") {
    return _higherWins(local, server);
  }

  if (strategy === "last_write_wins") {
    return _lastWriteWins(local, server);
  }

  // Fallback: higher_wins is always the safe default for an edtech platform
  return _higherWins(local, server);
}

/**
 * Keep the version with higher XP and better accuracy.
 * This ensures students NEVER lose progress they earned offline.
 */
function _higherWins(local, server) {
  const localXp  = Number(local?.xp_awarded   || 0);
  const serverXp = Number(server?.xp_awarded  || 0);
  const localAcc  = Number(local?.accuracy    || (local?.outcome  ? 1 : 0));
  const serverAcc = Number(server?.accuracy   || (server?.outcome ? 1 : 0));

  // Pick the record with higher XP; tie-break with accuracy
  if (localXp > serverXp) return local;
  if (serverXp > localXp) return server;

  // XP tied — prefer higher accuracy
  return localAcc >= serverAcc ? local : server;
}

/**
 * Last-write-wins: prefer the most recently timestamped record.
 */
function _lastWriteWins(local, server) {
  const localTs  = Number(local?.timestamp  || 0);
  const serverTs = Number(server?.timestamp || 0);
  return localTs >= serverTs ? local : server;
}

/**
 * Utility: merge two arrays of interactions, de-duplicating by interaction_id.
 * Used when a device comes online after a long offline period and needs to
 * merge its local log with what the server already has.
 *
 * @param {Array} localList  - Local interactions array
 * @param {Array} serverList - Server interactions array
 * @returns {Array}          - Merged, de-duplicated list
 */
export function mergeInteractionLists(localList = [], serverList = []) {
  const merged = new Map();

  // Server baseline first
  for (const item of serverList) {
    const key = item.interaction_id || item.id;
    if (key) merged.set(String(key), item);
  }

  // Local overrides using higher_wins per item
  for (const item of localList) {
    const key = item.interaction_id || item.id;
    if (!key) continue;
    const existing = merged.get(String(key));
    merged.set(String(key), existing ? _higherWins(item, existing) : item);
  }

  return Array.from(merged.values());
}
