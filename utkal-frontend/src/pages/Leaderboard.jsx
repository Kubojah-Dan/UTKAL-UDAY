import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { Trophy, Crown, Star, Zap, Medal } from "lucide-react";
import SyncStatusBanner from "../components/SyncStatusBanner";

const SCOPES = [
  { key: "class",    label: "My Class"  },
  { key: "school",   label: "School"    },
  { key: "district", label: "District"  },
  { key: "state",    label: "State"     },
];

const MEDAL_CONFIG = [
  { cls: "gold",   emoji: "🥇", label: "1" },
  { cls: "silver", emoji: "🥈", label: "2" },
  { cls: "bronze", emoji: "🥉", label: "3" },
];

function Podium({ top3 }) {
  if (!top3?.length) return null;
  const order = [top3[1], top3[0], top3[2]].filter(Boolean); // 2nd, 1st, 3rd
  const colors = ["silver", "gold", "bronze"];
  const heights = ["60px", "80px", "48px"];

  return (
    <div className="lb-podium">
      {order.map((student, i) => {
        const cfg = MEDAL_CONFIG[student.rank - 1] || MEDAL_CONFIG[2];
        return (
          <div key={student.student_id} className="lb-podium-slot">
            <div className={`lb-avatar ${cfg.cls}`}>
              {(student.name || "?")[0].toUpperCase()}
            </div>
            <div className="lb-name" title={student.name}>{student.name}</div>
            <div className="lb-xp">{student.total_xp?.toLocaleString()} XP</div>
            <div className={`lb-pedestal ${cfg.cls}`} style={{ height: heights[i] }}>
              {cfg.emoji}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function MeritBadge({ tier }) {
  if (!tier) return null;
  const labels = { legend: "👑 Legend", mentor: "🎓 Mentor", scholar: "📚 Scholar" };
  return <span className={`merit-badge ${tier}`}>{labels[tier]}</span>;
}

export default function Leaderboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [scope, setScope]       = useState("school");
  const [grade, setGrade]       = useState(user?.class_grade || "");
  const [rows, setRows]         = useState([]);
  const [myRank, setMyRank]     = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  const fetchLeaderboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let scopeValue = "";
      if (scope === "school" || scope === "class") scopeValue = user?.school || "";
      if (scope === "district") scopeValue = user?.district || "";

      const params = { scope, scope_value: scopeValue, limit: 50 };
      if (grade) params.grade = grade;

      const [lbRes, rankRes] = await Promise.all([
        api.get("/leaderboard", { params }),
        api.get("/leaderboard/my-rank", { params: { ...params, student_id: user?.id } }).catch(() => ({ data: null })),
      ]);

      setRows(lbRes.data?.rows || []);
      setMyRank(rankRes.data);
    } catch (e) {
      setError("Failed to load leaderboard. You may be offline.");
    } finally {
      setLoading(false);
    }
  }, [scope, grade]);

  useEffect(() => { fetchLeaderboard(); }, [fetchLeaderboard]);

  const top3 = rows.slice(0, 3);

  return (
    <div className="container notes-page">
      <SyncStatusBanner />

      {/* Header */}
      <div className="panel" style={{ background: "linear-gradient(135deg,#0f172a,#1e3a8a)", color: "#fff", border: "none" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <Trophy size={28} color="#f59e0b" />
          <div>
            <h2 style={{ margin: 0, color: "#fff" }}>Leaderboard</h2>
            <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.85rem" }}>
              See how you rank against your peers. Every XP counts!
            </p>
          </div>
        </div>

        {/* My rank callout */}
        {myRank?.found && (
          <div className="lb-my-rank-callout" style={{ background: "rgba(255,255,255,0.1)", color: "#e0f2fe", border: "1px solid rgba(255,255,255,0.2)" }}>
            <Zap size={16} style={{ display: "inline", marginRight: 6, color: "#f59e0b" }} />
            {myRank.motivation_message}
            {myRank.merit_tier && (
              <span style={{ marginLeft: 10 }}>
                <MeritBadge tier={myRank.merit_tier} />
              </span>
            )}
          </div>
        )}
        {myRank && !myRank.found && (
          <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: 8 }}>
            {myRank.motivation_message}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="panel" style={{ padding: "14px 18px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
          <div className="leaderboard-tabs">
            {SCOPES.map((s) => (
              <button
                key={s.key}
                className={`lb-tab ${scope === s.key ? "active" : ""}`}
                onClick={() => setScope(s.key)}
              >
                {s.label}
              </button>
            ))}
          </div>

          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="select-input"
            style={{ width: "auto", marginTop: 0 }}
          >
            <option value="">All Grades</option>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((g) => (
              <option key={g} value={g}>Grade {g}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Content */}
      {loading && <div className="panel"><p className="muted">Loading leaderboard…</p></div>}

      {error && <div className="panel"><p style={{ color: "var(--danger)" }}>{error}</p></div>}

      {!loading && !error && (
        <>
          {/* Podium */}
          {top3.length >= 1 && (
            <div className="panel">
              <h3 style={{ textAlign: "center", marginBottom: 0 }}>
                <Crown size={18} style={{ color: "#f59e0b", marginRight: 6 }} />
                Top Performers
              </h3>
              <Podium top3={top3} />
            </div>
          )}

          {/* Full table */}
          <div className="panel">
            <div className="panel-head">
              <h3 style={{ margin: 0 }}>Full Rankings</h3>
              <span className="muted" style={{ fontSize: "0.8rem" }}>
                {rows.length} students
              </span>
            </div>

            {rows.length === 0 ? (
              <p className="muted">No students on this leaderboard yet. Be the first!</p>
            ) : (
              <div className="lb-table">
                {rows.map((row) => {
                  const isMe = row.student_id === user?.id;
                  const rank = row.rank;
                  const rankEmoji = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : null;

                  return (
                    <div key={row.student_id} className={`lb-row ${isMe ? "my-rank" : ""}`}>
                      <div className="lb-rank-num">
                        {rankEmoji || `#${rank}`}
                      </div>
                      <div className="lb-row-name">
                        {row.name}
                        {isMe && <span style={{ marginLeft: 6, fontSize: "0.72rem", color: "var(--brand)" }}>(You)</span>}
                        {row.merit_tier && (
                          <span style={{ marginLeft: 6 }}>
                            <MeritBadge tier={row.merit_tier} />
                          </span>
                        )}
                      </div>
                      <div className="lb-row-xp">
                        <Zap size={12} style={{ color: "#f59e0b" }} /> {row.total_xp?.toLocaleString()} XP
                      </div>
                      {row.xp_gap_to_next > 0 && !isMe && (
                        <div className="lb-row-gap">
                          +{row.xp_gap_to_next} behind #{rank - 1}
                        </div>
                      )}
                      {isMe && row.xp_gap_to_next > 0 && (
                        <div className="lb-row-gap" style={{ background: "rgba(15,118,110,0.15)", color: "var(--brand-dark)" }}>
                          {row.xp_gap_to_next} XP to #{rank - 1}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Merit tier guide */}
          <div className="panel">
            <h3>🏅 Merit Unlock Tiers</h3>
            <p className="muted" style={{ marginBottom: 12 }}>
              Earn your place on the leaderboard to unlock exclusive features — free, based on merit.
            </p>
            <div style={{ display: "grid", gap: 10 }}>
              {[
                { tier: "scholar", label: "Scholar (Top 100)", features: "Harder questions, exclusive badge frame, priority doubt submission" },
                { tier: "mentor",  label: "Mentor (Top 50)",   features: "Submit study tips; earn XP when classmates use your tips" },
                { tier: "legend",  label: "Legend (Top 10)",   features: "Hall of Fame entry, special border, early feature access" },
              ].map(({ tier, label, features }) => (
                <div key={tier} className={`unlock-banner ${tier}`}>
                  <div style={{ fontSize: "1.5rem" }}>
                    {tier === "legend" ? "👑" : tier === "mentor" ? "🎓" : "📚"}
                  </div>
                  <div>
                    <strong>{label}</strong>
                    <p style={{ margin: 0, fontSize: "0.82rem", opacity: 0.85 }}>{features}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hall of Fame link */}
          <div className="panel" style={{ textAlign: "center" }}>
            <h3>🌟 Hall of Fame</h3>
            <p className="muted">See the all-time top students on Utkal Uday.</p>
            <button className="btn-primary" onClick={() => navigate("/hall-of-fame")}>
              View Hall of Fame
            </button>
          </div>
        </>
      )}
    </div>
  );
}
