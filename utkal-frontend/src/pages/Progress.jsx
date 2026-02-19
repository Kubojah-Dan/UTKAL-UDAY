import React, { useEffect, useState } from "react";
import { computeInteractionStats, getAllInteractions } from "../services/events";
import { useAuth } from "../context/AuthContext";

export default function Progress() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [interactions, setInteractions] = useState([]);

  useEffect(() => {
    (async () => {
      const [allInteractions, summary] = await Promise.all([
        getAllInteractions(300),
        computeInteractionStats(user.id)
      ]);
      setInteractions(allInteractions.filter((it) => it.student_id === user.id));
      setStats(summary);
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
        </div>
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
                  <strong>{accuracy}%</strong>
                </div>
                <div className="meter"><span style={{ width: `${Math.max(6, accuracy)}%` }} /></div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="panel">
        <h3>Recent Attempts</h3>
        <div className="recent-list">
          {interactions.slice(0, 20).map((it) => (
            <div key={it._id} className="recent-row">
              <div>
                <strong>{it.problem_id || it.quest_id}</strong>
                <small>{it.subject || "Unknown"} | skill {it.skill_id || "unknown"}</small>
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
