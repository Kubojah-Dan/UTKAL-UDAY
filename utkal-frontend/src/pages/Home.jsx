import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchRecommendations } from "../services/learning";
import { fetchBktParamsAndSave } from "../services/sync";
import { computeInteractionStats, getInteractionsByStudent } from "../services/events";
import { evaluateBadges } from "../services/gamification";
import SubjectIcon from "../components/SubjectIcon";
import BadgeIcon from "../components/BadgeIcon";
import { Trophy, Star, ChevronRight, Gamepad2, Bell } from "lucide-react";
import { api } from "../services/api";

export default function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [stats, setStats] = useState(null);
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setRefreshKey(prev => prev + 1);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await fetchBktParamsAndSave().catch(() => null);
        const [rec, localStats, interactions, notifs] = await Promise.all([
          fetchRecommendations(user.id, { limit: 6, grade: user.class_grade || undefined }),
          computeInteractionStats(user.id),
          getInteractionsByStudent(user.id),
          api.get('/tools/notifications', { params: { student_id: user.id, grade: user.class_grade } }).catch(() => ({ data: { notifications: [] } }))
        ]);
        setRecommendations(rec.quests || []);
        setStats(localStats);
        setGame(evaluateBadges(interactions || []));
        setNotifications(notifs.data.notifications || []);
      } catch (err) {
        console.warn("Failed to load student home data", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [user.id, user.class_grade, refreshKey]);

  return (
    <div className="container">
      {notifications.length > 0 && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-r-lg">
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-bold text-blue-900 mb-2">New Notifications</h3>
              {notifications.map((notif, idx) => (
                <div key={idx} className="mb-2 last:mb-0">
                  <p className="text-blue-800 font-semibold">{notif.title}</p>
                  <p className="text-blue-700 text-sm">{notif.message}</p>
                  {notif.quiz_id && (
                    <button
                      className="btn-primary small mt-2"
                      onClick={() => navigate(`/quiz/${notif.quiz_id}`)}
                    >
                      Start Quiz
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <section className="panel">
        <h2>Welcome, {user.name}</h2>
        <p className="muted">
          Continue your adaptive learning journey in Mathematics, Science, and English.
        </p>
        <p className="muted">
          {user.school ? `${user.school} - Grade ${user.class_grade || "?"}` : "Set your school profile in login."}
        </p>

        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <span>Total Attempts</span>
              <strong>{stats.total}</strong>
            </div>
            <div className="stat-card">
              <span>Accuracy</span>
              <strong>{Math.round((stats.accuracy || 0) * 100)}%</strong>
            </div>
            <div className="stat-card">
              <span>Average Time</span>
              <strong>{Math.round(stats.avgTime || 0)} ms</strong>
            </div>
            <div className="stat-card">
              <span>Total XP</span>
              <strong>{Math.round(stats.totalXp || 0)}</strong>
            </div>
            {game && (
              <>
                <div className="stat-card">
                  <span>Current Level</span>
                  <strong>Lv {game.level}</strong>
                </div>
                <div className="stat-card">
                  <span>Badges Earned</span>
                  <strong>{game.earnedCount}</strong>
                </div>
              </>
            )}
          </div>
        )}

        {game && (
          <div className="bg-gradient-to-br from-indigo-900 via-purple-900 to-indigo-950 p-6 rounded-2xl shadow-xl border border-indigo-700/50 mb-8 relative overflow-hidden">
            {/* Background decorative elements */}
            <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
              <Gamepad2 className="w-48 h-48 -rotate-12" />
            </div>

            <div className="flex flex-col md:flex-row gap-8 items-center relative z-10">
              {/* Level Badge Avatar */}
              <div className="relative group">
                <div className="absolute inset-0 bg-blue-500 rounded-full blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div className="w-24 h-24 rounded-full bg-gradient-to-b from-blue-400 to-indigo-600 p-1 relative z-10 shadow-inner">
                  <div className="w-full h-full rounded-full bg-slate-900 flex items-center justify-center flex-col border-2 border-indigo-900/50">
                    <span className="text-blue-300 text-xs font-bold uppercase tracking-wider">Level</span>
                    <span className="text-3xl font-black text-white drop-shadow-md">{game.level}</span>
                  </div>
                </div>
                {/* Floating Star */}
                <div className="absolute -bottom-2 -right-2 bg-amber-400 p-1.5 rounded-full shadow-lg border-2 border-slate-900 z-20">
                  <Star className="w-5 h-5 text-amber-900 fill-amber-700" />
                </div>
              </div>

              {/* Progress and Stats */}
              <div className="flex-1 w-full space-y-4">
                <div className="flex justify-between items-end">
                  <div>
                    <h3 className="text-xl font-bold text-white mb-1">Quest Progress</h3>
                    <p className="text-indigo-200 text-sm">{Math.round(stats?.totalXp || 0)} Total XP Earned</p>
                  </div>
                  <div className="text-right">
                    <span className="text-amber-400 font-bold text-xl">{Math.round(game.levelProgress.progressPct)}%</span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="relative h-4 bg-slate-800/80 rounded-full overflow-hidden border border-slate-700/50 shadow-inner">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 via-indigo-400 to-purple-500 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${Math.max(4, game.levelProgress.progressPct)}%` }}
                  >
                    {/* Shine effect */}
                    <div className="absolute top-0 left-0 w-full h-full bg-white opacity-20 transform -skew-x-12 translate-x-full animate-[shimmer_2s_infinite]"></div>
                  </div>
                </div>

                <p className="text-indigo-300 text-sm text-right">
                  {game.levelProgress.remainingXp} XP to reach <strong className="text-indigo-100">Level {game.level + 1}</strong>
                </p>
              </div>
            </div>
          </div>
        )}

        {game && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Trophy className="w-6 h-6 text-amber-500" />
              <h3 className="text-lg font-bold">Your Achievements</h3>
              <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-xs font-semibold ml-2">
                {game.earnedCount} Earned
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {game.badges.map((badge) => {
                const isEarned = badge.earned;
                return (
                  <div key={badge.id} className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${isEarned ? 'bg-white border-amber-200 shadow-md hover:shadow-lg hover:-translate-y-1' : 'bg-slate-50 border-slate-200 border-dashed opacity-70 grayscale'}`}>
                    {isEarned && (
                      <div className="absolute -top-3 -right-3">
                        <div className="relative">
                          <div className="absolute inset-0 bg-yellow-400 rounded-full blur animate-pulse"></div>
                          <Star className="w-8 h-8 text-yellow-400 fill-yellow-400 relative z-10 drop-shadow" />
                        </div>
                      </div>
                    )}
                    <div className={`mb-3 flex justify-center ${isEarned ? 'text-amber-500' : 'text-slate-400'}`}>
                      <BadgeIcon icon={badge.icon} className="w-12 h-12" />
                    </div>
                    <div className="text-center">
                      <strong className={`block mb-1 ${isEarned ? 'text-slate-800' : 'text-slate-500'}`}>{badge.title}</strong>
                      <small className="text-slate-500 text-xs leading-tight block">{badge.description}</small>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h3>Recommended Quests</h3>
          <button className="btn-outline small" onClick={() => navigate("/quest")}>Start Next Quest</button>
        </div>

        {loading && <p className="muted">Loading recommendations...</p>}
        {!loading && recommendations.length === 0 && (
          <p className="muted">No recommendations available yet. Start with any quest.</p>
        )}

        <div className="quest-grid">
          {recommendations.map((q) => (
            <article key={q.quest_id} className="quest-card">
              <div className="pill-row">
                <span className="pill with-icon"><SubjectIcon subject={q.subject} />{q.subject}</span>
                <span className="pill">Grade {q.grade}</span>
              </div>
              <h4>{q.skill_str || q.skill_id}</h4>
              <p className="muted">Difficulty: {q.difficulty || "adaptive"}</p>
              <button className="btn-primary small" onClick={() => navigate(`/quest/${q.quest_id}`)}>
                Attempt
              </button>
            </article>
          ))}
        </div>

        <div className="quick-links">
          <Link to="/skill-map" className="btn-outline">View Skill Map</Link>
          <Link to="/progress" className="btn-outline">View Progress</Link>
        </div>
      </section>
    </div>
  );
}
