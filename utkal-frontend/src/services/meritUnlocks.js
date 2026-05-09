/**
 * Merit unlock service — determines which features a student has unlocked
 * based on their leaderboard rank.
 *
 * Tiers:
 *   Top 100 → Scholar  — harder questions, exclusive badge frame, priority doubt
 *   Top 50  → Mentor   — submit tips/mnemonics for teacher approval
 *   Top 10  → Legend   — Hall of Fame entry, special border, early feature access
 */
import { api } from "./api";

/** Cached tier to avoid repeated API calls */
let _cachedTier = null;
let _cacheTs = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Fetch the student's current merit tier from the leaderboard API.
 * Returns 'legend' | 'mentor' | 'scholar' | null
 */
export async function getMeritTier(studentId, { grade, school } = {}) {
  if (_cachedTier !== null && Date.now() - _cacheTs < CACHE_TTL) {
    return _cachedTier;
  }
  try {
    const params = { scope: "school" };
    if (grade)  params.grade  = grade;
    if (school) params.scope_value = school;

    const res = await api.get("/leaderboard/my-rank", { params });
    _cachedTier = res.data?.merit_tier ?? null;
    _cacheTs    = Date.now();
    return _cachedTier;
  } catch {
    return null;
  }
}

/**
 * Get full rank info including motivational message.
 */
export async function getMyRankInfo(studentId, { grade, school } = {}) {
  try {
    const params = { scope: "school" };
    if (grade)  params.grade  = grade;
    if (school) params.scope_value = school;
    const res = await api.get("/leaderboard/my-rank", { params });
    return res.data;
  } catch {
    return null;
  }
}

/**
 * Returns the list of features unlocked for a given merit tier.
 */
export function getUnlockedFeatures(tier) {
  const features = {
    scholar: [
      "Access to harder challenge questions (one grade above your own)",
      "Exclusive Scholar badge frame on your profile",
      "Priority doubt submission to teachers",
      "Access to previous year exam question sets",
    ],
    mentor: [
      "All Scholar features",
      "Submit study tips and mnemonics for teacher approval",
      "Earn passive XP when your tips are used by other students",
    ],
    legend: [
      "All Scholar and Mentor features",
      "Permanent Hall of Fame entry",
      "Special Legend border on your profile",
      "Early access to new Utkal Uday features",
    ],
  };
  return features[tier] || [];
}

/**
 * Tier display config for UI rendering.
 */
export const TIER_CONFIG = {
  legend:  { label: "Legend",  emoji: "👑", color: "#f59e0b" },
  mentor:  { label: "Mentor",  emoji: "🎓", color: "#3b82f6" },
  scholar: { label: "Scholar", emoji: "📚", color: "#10b981" },
};

export function clearMeritCache() {
  _cachedTier = null;
  _cacheTs = 0;
}
