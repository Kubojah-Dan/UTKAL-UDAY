import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { Crown } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function HallOfFame() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [grade, setGrade] = useState(user?.class_grade || "");
  const [legends, setLegends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = { limit: 10 };
    if (grade) params.grade = grade;
    api.get("/leaderboard/hall-of-fame", { params })
      .then((res) => setLegends(res.data?.hall_of_fame || []))
      .catch(() => setLegends([]))
      .finally(() => setLoading(false));
  }, [grade]);

  return (
    <div className="container notes-page">
      {/* Header */}
      <div className="panel" style={{ background: "linear-gradient(135deg,#1e1b4b,#312e81)", color: "#fff", border: "none", textAlign: "center" }}>
        <div style={{ fontSize: "3rem", marginBottom: 8 }}>👑</div>
        <h2 style={{ margin: 0, color: "#fde68a" }}>Hall of Fame</h2>
        <p style={{ color: "#c4b5fd", marginTop: 6 }}>
          All-time top students of Utkal Uday. Earn your Legend status!
        </p>
        <div style={{ marginTop: 12 }}>
           <button 
             onClick={() => navigate("/certificates")}
             className="btn-primary"
             style={{ background: "#fde68a", color: "#1e1b4b", border: "none", fontWeight: "bold" }}
           >
             View My Certificates
           </button>
        </div>

        {/* Grade filter */}
        <div style={{ marginTop: 16 }}>
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            style={{ padding: "8px 14px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.1)", color: "#fff", fontSize: "0.9rem" }}
          >
            <option value="">All Grades</option>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((g) => (
              <option key={g} value={g} style={{ color: "#000" }}>Grade {g}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="panel"><p className="muted">Loading Hall of Fame…</p></div>}

      {!loading && legends.length === 0 && (
        <div className="panel" style={{ textAlign: "center" }}>
          <p className="muted">No legends yet for this grade. Be the first!</p>
        </div>
      )}

      {!loading && legends.length > 0 && (
        <div className="hof-grid">
          {legends.map((student) => {
            const rankEmoji = student.rank === 1 ? "👑" : student.rank === 2 ? "🥈" : student.rank === 3 ? "🥉" : "⭐";
            const isMe = student.student_id === user?.id;
            return (
              <div key={student.student_id} className="hof-card" style={isMe ? { outline: "2px solid #fde68a" } : {}}>
                <div className="hof-crown">{rankEmoji}</div>
                <div className="hof-name">
                  {student.name}
                  {isMe && <span style={{ fontSize: "0.72rem", color: "#fde68a", marginLeft: 4 }}>(You!)</span>}
                </div>
                <div className="hof-grade">Grade {student.grade} · {student.school || "Unknown School"}</div>
                <div className="hof-xp">{student.total_xp?.toLocaleString()} XP</div>
                <div style={{ marginTop: 8, fontSize: "0.75rem", color: "#a5b4fc" }}>
                  #{student.rank} · Lv {student.level}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="panel" style={{ textAlign: "center", marginTop: 16 }}>
        <Crown size={20} style={{ color: "#f59e0b", marginBottom: 8 }} />
        <h3>How to reach the Hall of Fame</h3>
        <p className="muted">Reach the Top 10 on the State leaderboard in your grade. Every answer, every day counts.</p>
      </div>
    </div>
  );
}
