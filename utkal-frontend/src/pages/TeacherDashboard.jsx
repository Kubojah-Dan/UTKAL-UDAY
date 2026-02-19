import React, { useEffect, useState } from "react";
import { fetchTeacherAnalytics } from "../services/teacher";

function pct(value) {
  return Math.round((value || 0) * 100);
}

export default function TeacherDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTeacherAnalytics()
      .then(setData)
      .catch((err) => {
        setError(err?.response?.data?.detail || "Unable to load analytics.");
      });
  }, []);

  if (error) {
    return <div className="container"><div className="panel error-text">{error}</div></div>;
  }

  if (!data) {
    return <div className="container"><div className="panel">Loading teacher analytics...</div></div>;
  }

  const overview = data.overview || {};

  return (
    <div className="container">
      <section className="panel">
        <h2>Teacher Dashboard</h2>
        <p className="muted">Track class performance and identify learning gaps quickly.</p>
        <div className="stats-grid">
          <div className="stat-card"><span>Students</span><strong>{overview.total_students}</strong></div>
          <div className="stat-card"><span>Attempts</span><strong>{overview.total_attempts}</strong></div>
          <div className="stat-card"><span>Overall Accuracy</span><strong>{pct(overview.overall_accuracy)}%</strong></div>
          <div className="stat-card"><span>Avg Time</span><strong>{Math.round(overview.avg_time_ms || 0)} ms</strong></div>
        </div>
      </section>

      <section className="panel">
        <h3>Subject Breakdown</h3>
        <div className="bar-list">
          {(data.subject_breakdown || []).map((item) => {
            const accuracy = pct(item.accuracy);
            return (
              <div key={item.subject} className="bar-item">
                <div className="bar-meta">
                  <span>{item.subject}</span>
                  <strong>{accuracy}% ({item.attempts} attempts)</strong>
                </div>
                <div className="meter"><span style={{ width: `${Math.max(5, accuracy)}%` }} /></div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="panel">
        <h3>Top Student Activity</h3>
        <div className="table-wrap">
          <table className="clean-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Attempts</th>
                <th>Accuracy</th>
                <th>Avg Time</th>
              </tr>
            </thead>
            <tbody>
              {(data.student_progress || []).slice(0, 15).map((row) => (
                <tr key={row.student_id}>
                  <td>{row.student_id}</td>
                  <td>{row.attempts}</td>
                  <td>{pct(row.accuracy)}%</td>
                  <td>{Math.round(row.avg_time_ms || 0)} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h3>Recent Activity</h3>
        <div className="recent-list">
          {(data.recent_activity || []).slice(0, 20).map((row, idx) => (
            <div key={`${row.student_id}-${row.timestamp}-${idx}`} className="recent-row">
              <div>
                <strong>{row.student_id}</strong>
                <small>{row.subject || "Unknown"} | {row.quest_id}</small>
              </div>
              <div className={`result-chip ${row.outcome ? "ok" : "bad"}`}>
                {row.outcome ? "Correct" : "Incorrect"}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
