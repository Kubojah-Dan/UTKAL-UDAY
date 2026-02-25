import React, { useEffect, useState } from "react";
import { computeInteractionStats, getAllInteractions } from "../services/events";
import { useAuth } from "../context/AuthContext";
import { evaluateBadges } from "../services/gamification";
import SubjectIcon from "../components/SubjectIcon";
import BadgeIcon from "../components/BadgeIcon";

export default function Progress() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [game, setGame] = useState(null);

  useEffect(() => {
    (async () => {
      const [allInteractions, summary] = await Promise.all([
        getAllInteractions(300),
        computeInteractionStats(user.id)
      ]);
      const mine = allInteractions.filter((it) => it.student_id === user.id);
      setInteractions(mine);
      setStats(summary);
      setGame(evaluateBadges(mine));
    })();
  }, [user.id]);

  if (!stats) {
    return <div className="container"><div className="panel">Loading progress...</div></div>;
  }

  return (
    <div className="container">
      <section className="panel">
        <h2>My Progress</h2>
        <div className="stats-grid">
          <div className="stat-card"><span>Attempts</span><strong>{stats.total}</strong></div>
          <div className="stat-card"><span>Correct</span><strong>{stats.correct}</strong></div>
          <div className="stat-card"><span>Accuracy</span><strong>{Math.round((stats.accuracy || 0) * 100)}%</strong></div>
          <div className="stat-card"><span>Avg Time</span><strong>{Math.round(stats.avgTime || 0)} ms</strong></div>
          <div className="stat-card"><span>Total XP</span><strong>{Math.round(stats.totalXp || 0)}</strong></div>
          {game && <div className="stat-card"><span>Current Level</span><strong>Lv {game.level}</strong></div>}
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

      {game && (
        <section className="panel">
          <h3>Badges and Levels</h3>
          <p className="muted">Earn badges by staying consistent, accurate, and fast.</p>
          <div className="badge-grid">
            {game.badges.map((badge) => (
              <div key={badge.id} className={`badge-card ${badge.earned ? "earned" : "locked"}`}>
                <div className="badge-title"><BadgeIcon icon={badge.icon} /><strong>{badge.title}</strong></div>
                <small>{badge.description}</small>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel">
        <h3>Recent Attempts</h3>
        <div className="recent-list">
          {interactions.slice(0, 20).map((it) => (
            <div key={it._id} className="recent-row">
              <div>
                <strong>{it.problem_id || it.quest_id}</strong>
                <small>{it.subject || "Unknown"} | skill {it.skill_id || "unknown"} | +{Number(it.xp_awarded || 0)} XP</small>
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
