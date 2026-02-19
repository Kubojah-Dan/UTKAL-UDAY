import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchRecommendations } from "../services/learning";
import { fetchBktParamsAndSave } from "../services/sync";
import { computeInteractionStats } from "../services/events";

export default function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await fetchBktParamsAndSave().catch(() => null);
        const [rec, localStats] = await Promise.all([
          fetchRecommendations(user.id, { limit: 6 }),
          computeInteractionStats(user.id)
        ]);
        setRecommendations(rec.quests || []);
        setStats(localStats);
      } catch (err) {
        console.warn("Failed to load student home data", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [user.id]);

  return (
    <div className="container">
      <section className="panel">
        <h2>Welcome, {user.name}</h2>
        <p className="muted">
          Continue your adaptive learning journey in Mathematics and Science.
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
                <span className="pill">{q.subject}</span>
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
