import React, { useEffect, useState, useCallback } from "react";
import { computeInteractionStats, getAllInteractions } from "../services/events";
import { useAuth } from "../context/AuthContext";
import { evaluateBadges } from "../services/gamification";
import SubjectIcon from "../components/SubjectIcon";
import BadgeIcon from "../components/BadgeIcon";
import { api } from "../services/api";
import { Trophy, Medal, Crown, Users, School, Globe, Flame } from "lucide-react";
import { useNavigate } from "react-router-dom";
import StreakBadge from "../components/StreakBadge";

const RANK_ICONS = [
  <Crown size={18} style={{ color: "#f59e0b" }} />,
  <Medal size={18} style={{ color: "#94a3b8" }} />,
  <Medal size={18} style={{ color: "#b45309" }} />,
];

function RankBadge({ rank }) {
  if (rank <= 3) return <span className="rank-icon">{RANK_ICONS[rank - 1]}</span>;
  return <span className="rank-number">#{rank}</span>;
}

function LevelBadge({ level }) {
  const color = level >= 10 ? "#7c3aed" : level >= 5 ? "#0f766e" : "#64748b";
  return (
    <span className="lb-level" style={{ background: color }}>
      Lv {level}
    </span>
  );
}

export default function Progress() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [game, setGame] = useState(null);

  // Leaderboard state
  const [leaderboard, setLeaderboard] = useState([]);
  const [lbScope, setLbScope] = useState("school"); // "school" | "all"
  const [lbLoading, setLbLoading] = useState(false);
  const [myRank, setMyRank] = useState(null);

  // Load personal stats
  useEffect(() => {
    (async () => {
      const [allInteractions, summary] = await Promise.all([
        getAllInteractions(300),
        computeInteractionStats(user.id),
      ]);
      const mine = allInteractions.filter((it) => it.student_id === user.id);
      setInteractions(mine);
      setStats(summary);
      const g = evaluateBadges(mine);
      setGame(g);

      // Push latest stats to leaderboard
      if (user.class_grade) {
        try {
          await api.post("/leaderboard/update", {
            student_id: user.id,
            name: user.name,
            school: user.school || "",
            grade: user.class_grade,
            total_xp: Math.round(summary.totalXp || 0),
            level: g.level,
            badges_earned: g.earnedCount,
            accuracy: summary.accuracy || 0,
            total_attempts: summary.total || 0,
          });
        } catch (_) {}
      }
    })();
  }, [user.id, user.class_grade, user.name, user.school]);

  // Load leaderboard
  const loadLeaderboard = useCallback(async (scope) => {
    if (!user.class_grade) return;
    setLbLoading(true);
    try {
      const params = { grade: user.class_grade };
      if (scope === "school" && user.school) params.school = user.school;
      const res = await api.get("/leaderboard", { params });
      const rows = res.data?.rows || [];
      setLeaderboard(rows);
      const idx = rows.findIndex((r) => r.student_id === user.id);
      setMyRank(idx >= 0 ? idx + 1 : null);
    } catch (_) {
      setLeaderboard([]);
    } finally {
      setLbLoading(false);
    }
  }, [user.class_grade, user.school, user.id]);

  useEffect(() => {
    loadLeaderboard(lbScope);
  }, [lbScope, loadLeaderboard]);

  if (!stats) {
    return <div className="container"><div className="panel">Loading progress...</div></div>;
  }

  return (
    <div className="container">

      {/* Personal Stats */}
      <section className="panel">
        <h2>My Progress</h2>
        <div className="stats-grid">
          <div className="stat-card"><span>Attempts</span><strong>{stats.total}</strong></div>
          <div className="stat-card"><span>Correct</span><strong>{stats.correct}</strong></div>
          <div className="stat-card"><span>Accuracy</span><strong>{Math.round((stats.accuracy || 0) * 100)}%</strong></div>
          <div className="stat-card"><span>Total XP</span><strong>{Math.round(stats.totalXp || 0)}</strong></div>
          {game && <div className="stat-card"><span>Level</span><strong>Lv {game.level}</strong></div>}
          {myRank && <div className="stat-card"><span>My Rank</span><strong>#{myRank}</strong></div>}
        </div>
        {game && (
          <div className="level-progress">
            <div className="bar-meta">
              <span>Level Progress</span>
              <strong>{Math.round(game.levelProgress.progressPct)}%</strong>
            </div>
            <div className="meter"><span style={{ width: `${Math.max(4, game.levelProgress.progressPct)}%` }} /></div>
            <small className="muted">{game.levelProgress.remainingXp} XP to level {game.level + 1}</small>
          </div>
        )}
      </section>

      {/* Leaderboard */}
      <section className="panel">
        <div className="lb-header">
          <div className="lb-title-row">
            <Trophy size={20} style={{ color: "#f59e0b" }} />
            <h3>Leaderboard — Grade {user.class_grade}</h3>
          </div>
          <div className="lb-scope-toggle">
            <button
              className={`lb-scope-btn ${lbScope === "school" ? "active" : ""}`}
              onClick={() => setLbScope("school")}
            >
              <School size={14} /> My School
            </button>
            <button
              className={`lb-scope-btn ${lbScope === "all" ? "active" : ""}`}
              onClick={() => setLbScope("all")}
            >
              <Globe size={14} /> All Schools
            </button>
          </div>
        </div>

        {lbLoading && <p className="muted" style={{ marginTop: 12 }}>Loading leaderboard...</p>}

        {!lbLoading && leaderboard.length === 0 && (
          <div className="lb-empty">
            <Users size={40} style={{ color: "#cbd5e1", marginBottom: 8 }} />
            <p>No students found yet.</p>
            <small>Be the first! Complete quests to appear here.</small>
          </div>
        )}

        {!lbLoading && leaderboard.length > 0 && (
          <div className="lb-table">
            {/* Top 3 podium */}
            {leaderboard.length >= 1 && (
              <div className="lb-podium">
                {leaderboard.slice(0, Math.min(3, leaderboard.length)).map((row, i) => (
                  <div
                    key={row.student_id}
                    className={`podium-card podium-${i + 1} ${row.student_id === user.id ? "podium-me" : ""}`}
                  >
                    <div className="podium-rank">{RANK_ICONS[i]}</div>
                    <div className="podium-avatar">{row.name?.[0]?.toUpperCase() || "?"}</div>
                    <div className="podium-name">{row.student_id === user.id ? "You" : row.name}</div>
                    <div className="podium-xp">{row.total_xp} XP</div>
                    <LevelBadge level={row.level} />
                  </div>
                ))}
              </div>
            )}

            {/* Full list */}
            <div className="lb-list">
              {leaderboard.map((row, i) => {
                const isMe = row.student_id === user.id;
                return (
                  <div key={row.student_id} className={`lb-row ${isMe ? "lb-row-me" : ""}`}>
                    <RankBadge rank={i + 1} />
                    <div className="lb-avatar">{row.name?.[0]?.toUpperCase() || "?"}</div>
                    <div className="lb-info">
                      <span className="lb-name">
                        {isMe ? <strong>You ({row.name})</strong> : row.name}
                      </span>
                      {lbScope === "all" && row.school && (
                        <small className="lb-school">{row.school}</small>
                      )}
                    </div>
                    <div className="lb-stats">
                      <LevelBadge level={row.level} />
                      <span className="lb-xp">{row.total_xp} XP</span>
                      <span className="lb-badges">{row.badges_earned} 🏅</span>
                      <span className="lb-accuracy">{Math.round((row.accuracy || 0) * 100)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* Subject Accuracy */}
      <section className="panel">
        <h3>Subject Accuracy</h3>
        <div className="bar-list">
          {Object.entries(stats.perSubject || {}).map(([subject, value]) => {
            const accuracy = Math.round((value.correct / Math.max(1, value.attempts)) * 100);
            return (
              <div key={subject} className="bar-item">
                <div className="bar-meta">
                  <span>{subject}</span>
                  <span className="subject-inline-icon"><SubjectIcon subject={subject} /></span>
                  <strong>{accuracy}%</strong>
                </div>
                <div className="meter"><span style={{ width: `${Math.max(6, accuracy)}%` }} /></div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Streak Badges Section */}
      {game && (
        <section className="panel" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)", border: "none", color: "white" }}>
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-white m-0">Consistency Badges</h3>
              <p className="text-slate-400 text-sm mt-1">Unlock LeetCode-style badges by learning every day.</p>
            </div>
            <div className="bg-orange-500/10 text-orange-400 px-4 py-2 rounded-2xl flex items-center gap-2 border border-orange-500/20">
               <Flame className="w-5 h-5" />
               <span className="font-bold">2026 Season</span>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-10 justify-center py-4">
            <StreakBadge days={50} earned={game.badges.find(b => b.id === "daily-50")?.earned} />
            <StreakBadge days={100} earned={game.badges.find(b => b.id === "daily-100")?.earned} />
            <StreakBadge days={200} earned={game.badges.find(b => b.id === "daily-200")?.earned} />
            <StreakBadge days={365} earned={game.badges.find(b => b.id === "daily-365")?.earned} />
          </div>
        </section>
      )}

      {/* Certificates Banner */}
      <section 
        className="panel group cursor-pointer overflow-hidden relative" 
        style={{ background: "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)", border: "1px solid #bbf7d0" }}
        onClick={() => navigate("/certificates")}
      >
        <div className="relative z-10 flex flex-col md:flex-row items-center gap-6">
          <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-lg shadow-emerald-200/50 shrink-0">
             <Trophy className="w-10 h-10 text-emerald-600" />
          </div>
          <div className="text-center md:text-left flex-grow">
             <h3 className="text-emerald-900 mb-1">Hall of Fame Certificates</h3>
             <p className="text-emerald-700/70 text-sm">Download your official academic certificates for Top 10 ranks and yearly achievements.</p>
          </div>
          <button className="btn-primary bg-emerald-600 hover:bg-emerald-700 border-none px-8">
            View My Certificates
          </button>
        </div>
        <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/3 opacity-5 group-hover:opacity-10 transition-opacity">
            <Trophy size={200} />
        </div>
      </section>

      {/* Badges */}
      {game && (
        <section className="panel">
          <h3>Other Achievements</h3>
          <p className="muted">Earn badges by staying accurate and fast in quests.</p>
          <div className="badge-grid">
            {game.badges.filter(b => !b.isPremium).map((badge) => (
              <div key={badge.id} className={`badge-card ${badge.earned ? "earned" : "locked"}`}>
                <div className="badge-title"><BadgeIcon icon={badge.icon} /><strong>{badge.title}</strong></div>
                <small>{badge.description}</small>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recent Attempts */}
      <section className="panel">
        <h3>Recent Attempts</h3>
        <div className="recent-list">
          {interactions.slice(0, 20).map((it) => (
            <div key={it._id} className="recent-row">
              <div>
                <strong>{it.problem_id || it.quest_id}</strong>
                <small>{it.subject || "Unknown"} | +{Number(it.xp_awarded || 0)} XP</small>
              </div>
              <div className={`result-chip ${it.outcome ? "ok" : "bad"}`}>
                {it.outcome ? "Correct" : "Incorrect"}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
