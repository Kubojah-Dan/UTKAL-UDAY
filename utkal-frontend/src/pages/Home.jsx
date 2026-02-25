import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchRecommendations } from "../services/learning";
import { fetchBktParamsAndSave } from "../services/sync";
import { computeInteractionStats, getInteractionsByStudent } from "../services/events";
import { evaluateBadges } from "../services/gamification";
import SubjectIcon from "../components/SubjectIcon";
import BadgeIcon from "../components/BadgeIcon";

export default function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [stats, setStats] = useState(null);
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await fetchBktParamsAndSave().catch(() => null);
        const [rec, localStats, interactions] = await Promise.all([
          fetchRecommendations(user.id, { limit: 6, grade: user.class_grade || undefined }),
          computeInteractionStats(user.id),
          getInteractionsByStudent(user.id)
        ]);
        setRecommendations(rec.quests || []);
        setStats(localStats);
        setGame(evaluateBadges(interactions || []));
      } catch (err) {
        console.warn("Failed to load student home data", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [user.id, user.class_grade]);

  return (
    <div className="container">
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
          <div className="level-progress">
            <div className="bar-meta">
              <span>Level progress</span>
              <strong>{Math.round(game.levelProgress.progressPct)}%</strong>
            </div>
            <div className="meter"><span style={{ width: `${Math.max(4, game.levelProgress.progressPct)}%` }} /></div>
            <small className="muted">{game.levelProgress.remainingXp} XP to next level</small>
          </div>
        )}

        {game && (
          <div className="badge-grid">
            {game.badges.map((badge) => (
              <div key={badge.id} className={`badge-card ${badge.earned ? "earned" : "locked"}`}>
                <div className="badge-title"><BadgeIcon icon={badge.icon} /><strong>{badge.title}</strong></div>
                <small>{badge.description}</small>
              </div>
            ))}
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
