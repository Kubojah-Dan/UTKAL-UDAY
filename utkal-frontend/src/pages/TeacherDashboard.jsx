import React, { useEffect, useMemo, useState } from "react";
import { fetchTeacherAnalytics } from "../services/teacher";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';

function pct(value) {
  return Math.round((value || 0) * 100);
}

function TrendChart({ points }) {
  if (!points || points.length === 0) {
    return <p className="muted">No trend data available for the selected filter.</p>;
  }

  // Map accuracy to a 0-100 scale for plotting
  const data = points.map(p => ({
    ...p,
    accuracyPct: Math.round((Number(p.accuracy) || 0) * 100)
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div className="bg-white border shadow-elevated p-3 rounded-lg text-sm">
          <p className="font-bold mb-1">{label}</p>
          <p className="text-teal-700">Attempts: {dataPoint.attempts}</p>
          <p className="text-sky-600">Accuracy: {dataPoint.accuracyPct}%</p>
          <p className="text-amber-600 mt-1">XP: {Math.round(dataPoint.xp || 0)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="trend-chart w-full" style={{ height: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} dy={10} />
          <YAxis yAxisId="left" orientation="left" stroke="#0f766e" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} dx={-10} />
          <YAxis yAxisId="right" orientation="right" stroke="#0ea5e9" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} dx={10} domain={[0, 100]} />
          <Tooltip content={<CustomTooltip />} />
          <Line yAxisId="left" type="monotone" dataKey="attempts" stroke="#0f766e" strokeWidth={3} activeDot={{ r: 8 }} name="Attempts" />
          <Line yAxisId="right" type="monotone" dataKey="accuracyPct" stroke="#0ea5e9" strokeWidth={3} name="Accuracy (%)" />
        </LineChart>
      </ResponsiveContainer>
      <div className="trend-key mt-4 flex gap-4 justify-center text-sm font-medium">
        <span className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-teal-700" />Attempts</span>
        <span className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-sky-500" />Accuracy</span>
      </div>
    </div>
  );
}

function riskColor(risk) {
  if (risk === "high") return "#dc2626";
  if (risk === "medium") return "#d97706";
  return "#0f766e";
}

function DependencyGraph({ graph }) {
  const [selectedId, setSelectedId] = useState(null);

  const model = useMemo(() => {
    const nodes = graph?.nodes || [];
    const edges = graph?.edges || [];
    if (!nodes.length) return null;

    const width = 920;
    const height = 380;
    const padX = 58;
    const padY = 36;

    const indegree = {};
    const level = {};
    nodes.forEach((n) => {
      indegree[n.id] = 0;
      level[n.id] = 0;
    });
    edges.forEach((e) => {
      if (e.target in indegree) indegree[e.target] += 1;
    });

    const starters = nodes.filter((n) => indegree[n.id] === 0).map((n) => n.id);
    const queue = starters.length ? starters : nodes.map((n) => n.id);
    const bySource = {};
    edges.forEach((e) => {
      bySource[e.source] = bySource[e.source] || [];
      bySource[e.source].push(e.target);
    });

    for (let i = 0; i < queue.length; i += 1) {
      const source = queue[i];
      const next = bySource[source] || [];
      next.forEach((target) => {
        level[target] = Math.max(level[target] || 0, (level[source] || 0) + 1);
        queue.push(target);
      });
    }

    const maxLevel = Math.max(0, ...Object.values(level));
    const levelGroups = {};
    nodes.forEach((n) => {
      const lv = level[n.id] || 0;
      levelGroups[lv] = levelGroups[lv] || [];
      levelGroups[lv].push(n);
    });

    const positioned = {};
    Object.entries(levelGroups).forEach(([lvRaw, group]) => {
      const lv = Number(lvRaw);
      const x = padX + (maxLevel === 0 ? 0 : (lv / maxLevel) * (width - padX * 2));
      const sorted = [...group].sort((a, b) => (a.gpa - b.gpa) || (b.attempts - a.attempts));
      const dy = sorted.length > 1 ? (height - padY * 2) / (sorted.length - 1) : 0;
      sorted.forEach((node, idx) => {
        positioned[node.id] = {
          ...node,
          x,
          y: sorted.length === 1 ? height / 2 : padY + idx * dy,
        };
      });
    });

    return { width, height, nodes: positioned, edges };
  }, [graph]);

  if (!model) {
    return <p className="muted">No dependency graph available for this filter.</p>;
  }

  const selected = selectedId ? model.nodes[selectedId] : null;

  return (
    <div className="dependency-wrap">
      <svg viewBox={`0 0 ${model.width} ${model.height}`} aria-label="Skill dependency graph">
        {model.edges.map((e) => {
          const src = model.nodes[e.source];
          const dst = model.nodes[e.target];
          if (!src || !dst) return null;
          return (
            <line
              key={`${e.source}-${e.target}`}
              x1={src.x}
              y1={src.y}
              x2={dst.x}
              y2={dst.y}
              stroke="#94a3b8"
              strokeWidth={Math.max(1.2, Number(e.weight || 0.2) * 3)}
              opacity={0.8}
            />
          );
        })}

        {Object.values(model.nodes).map((n) => (
          <g key={n.id} onClick={() => setSelectedId(n.id)} style={{ cursor: "pointer" }}>
            <circle
              cx={n.x}
              cy={n.y}
              r={selectedId === n.id ? 11 : 8}
              fill={riskColor(n.risk)}
              opacity={0.88}
            />
            <text x={n.x + 12} y={n.y + 4} fontSize="10" fill="#0f172a">
              {String(n.label).slice(0, 34)}
            </text>
          </g>
        ))}
      </svg>

      <div className="dependency-legend">
        <span><i className="risk-dot low" />Low risk</span>
        <span><i className="risk-dot medium" />Medium risk</span>
        <span><i className="risk-dot high" />High risk</span>
      </div>

      {selected && (
        <div className="dependency-focus">
          <strong>{selected.label}</strong>
          <small>{selected.attempts} attempts</small>
          <small>{pct(selected.accuracy)}% accuracy</small>
          <small>GPA {selected.gpa}</small>
        </div>
      )}
    </div>
  );
}

export default function TeacherDashboard() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [school, setSchool] = useState(user?.school || "");
  const [classGrade, setClassGrade] = useState(user?.class_grade ? String(user.class_grade) : "");
  const [trendDays, setTrendDays] = useState("30");

  useEffect(() => {
    setSchool(user?.school || "");
    setClassGrade(user?.class_grade ? String(user.class_grade) : "");
  }, [user?.school, user?.class_grade]);

  const [genTopic, setGenTopic] = useState("");
  const [genGrade, setGenGrade] = useState("3");
  const [genSubject, setGenSubject] = useState("Mathematics");
  const [genCount, setGenCount] = useState("5");
  const [genLoading, setGenLoading] = useState(false);
  const [genQuestions, setGenQuestions] = useState([]);
  const [activeTab, setActiveTab] = useState("analytics");

  const handleGenerate = async () => {
    setGenLoading(true);
    try {
      const res = await api.post("/tools/generate-questions", {
        topic: genTopic,
        grade: Number(genGrade),
        subject: genSubject,
        count: Number(genCount)
      });
      setGenQuestions(res.data || []);
      showToast("Questions generated successfully", "success");
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Unknown error";
      showToast("Failed to generate questions: " + msg, "error");
    } finally {
      setGenLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError("");

    fetchTeacherAnalytics({
      school: school || undefined,
      classGrade: classGrade ? Number(classGrade) : undefined,
      recentLimit: 40,
      trendDays: Number(trendDays)
    })
      .then((payload) => {
        if (!isMounted) return;
        setData(payload);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err?.response?.data?.detail || "Unable to load analytics.");
      })
      .finally(() => {
        if (!isMounted) return;
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [school, classGrade, trendDays]);

  const gradeOptions = useMemo(() => {
    const fromApi = data?.filter_options?.class_grades || [];
    const fallback = Array.from({ length: 12 }, (_, idx) => idx + 1);
    return [...new Set([...(fromApi.length ? fromApi : fallback), ...(classGrade ? [Number(classGrade)] : [])])]
      .filter((x) => Number.isFinite(Number(x)))
      .sort((a, b) => a - b);
  }, [data?.filter_options?.class_grades, classGrade]);

  if (error) {
    return <div className="container"><div className="panel error-text">{error}</div></div>;
  }

  if (loading && !data) {
    return <div className="container"><div className="panel">Loading teacher analytics...</div></div>;
  }

  const overview = data?.overview || {};
  const selectedFilters = data?.filters || {};
  const xai = data?.xai || {};

  return (
    <div className="container">
      <div className="tab-nav mb-6 flex gap-4 border-b">
        <button
          className={`px-4 py-2 ${activeTab === 'analytics' ? 'border-b-2 border-teal-700 font-bold' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
        </button>
        <button
          className={`px-4 py-2 ${activeTab === 'content' ? 'border-b-2 border-teal-700 font-bold' : ''}`}
          onClick={() => setActiveTab('content')}
        >
          Content Management (AI)
        </button>
      </div>

      {activeTab === 'analytics' ? (
        <>
          <section className="panel">
            <h2>Teacher Dashboard</h2>
            <p className="muted">Monitor progress by school and grade, then intervene quickly.</p>

            <div className="filter-grid">
              <label>
                School
                <select value={school} onChange={(e) => setSchool(e.target.value)} className="select-input">
                  {data?.filter_options?.schools?.length === 0 && <option value={school}>{school || "Select"}</option>}
                  {(data?.filter_options?.schools || []).map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </label>

              <label>
                Class Grade
                <select value={classGrade} onChange={(e) => setClassGrade(e.target.value)} className="select-input">
                  {gradeOptions.map((grade) => (
                    <option key={grade} value={grade}>Grade {grade}</option>
                  ))}
                </select>
              </label>

              <label>
                Trend Window
                <select value={trendDays} onChange={(e) => setTrendDays(e.target.value)} className="select-input">
                  <option value="14">14 days</option>
                  <option value="30">30 days</option>
                  <option value="60">60 days</option>
                  <option value="90">90 days</option>
                </select>
              </label>
            </div>

            <small className="muted">
              Viewing: {selectedFilters.school || "All schools"} | Grade {selectedFilters.class_grade || "All"}
            </small>

            <div className="stats-grid">
              <div className="stat-card"><span>Students</span><strong>{overview.total_students || 0}</strong></div>
              <div className="stat-card"><span>Attempts</span><strong>{overview.total_attempts || 0}</strong></div>
              <div className="stat-card"><span>Overall Accuracy</span><strong>{pct(overview.overall_accuracy)}%</strong></div>
              <div className="stat-card"><span>Avg Time</span><strong>{Math.round(overview.avg_time_ms || 0)} ms</strong></div>
              <div className="stat-card"><span>Total XP</span><strong>{Math.round(overview.total_xp || 0)}</strong></div>
            </div>
          </section>

          <section className="panel">
            <h3>Daily Activity Trend</h3>
            <TrendChart points={data?.daily_trend || []} />
          </section>

          <section className="panel">
            <h3>XAI Dependency Graph</h3>
            <p className="muted">Prerequisite chains and risk levels inferred from interaction outcomes.</p>
            <DependencyGraph graph={xai.graph} />
          </section>

          <section className="panel">
            <h3>Root Cause Skills</h3>
            <div className="table-wrap">
              <table className="clean-table">
                <thead>
                  <tr>
                    <th>Skill</th>
                    <th>Attempts</th>
                    <th>Accuracy</th>
                    <th>GPA</th>
                    <th>Risk</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(xai.root_causes || []).slice(0, 12).map((row) => (
                    <tr key={row.skill_id}>
                      <td>{row.skill_label}</td>
                      <td>{row.attempts}</td>
                      <td>{pct(row.accuracy)}%</td>
                      <td>{row.gpa}</td>
                      <td>{row.risk}</td>
                      <td>{row.recommended_action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h3>Prerequisite GPA Gaps</h3>
            <div className="table-wrap">
              <table className="clean-table">
                <thead>
                  <tr>
                    <th>Prerequisite</th>
                    <th>Dependent</th>
                    <th>Prereq GPA</th>
                    <th>Dependent GPA</th>
                    <th>Gap</th>
                    <th>Support</th>
                  </tr>
                </thead>
                <tbody>
                  {(xai.prerequisite_gaps || []).slice(0, 16).map((row, idx) => (
                    <tr key={`${row.prerequisite_id}-${row.dependent_id}-${idx}`}>
                      <td>{row.prerequisite_label}</td>
                      <td>{row.dependent_label}</td>
                      <td>{row.prerequisite_gpa}</td>
                      <td>{row.dependent_gpa}</td>
                      <td>{row.gap}</td>
                      <td>{row.support}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h3>Causal Chains</h3>
            <div className="chain-grid">
              {(xai.causal_chains || []).slice(0, 9).map((chain, idx) => (
                <article className="chain-card" key={`chain-${idx}`}>
                  <strong>{chain.weakest_skill}</strong>
                  <small>Avg GPA {chain.avg_gpa} | Confidence {Math.round((chain.confidence || 0) * 100)}%</small>
                  <p>{(chain.path || []).join(" -> ")}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel w-full">
            <h3>Subject Breakdown</h3>
            <div style={{ width: '100%', height: 350 }}>
              <ResponsiveContainer>
                <BarChart
                  data={(data?.subject_breakdown || []).map(item => ({ ...item, accuracyPct: pct(item.accuracy) }))}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 40, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} opacity={0.3} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="subject"
                    tick={{ fontSize: 13, fontWeight: "bold", fill: "#334155" }}
                    width={80}
                  />
                  <Tooltip
                    cursor={{ fill: "#f8fafc" }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white border shadow-elevated p-3 rounded-lg text-sm">
                            <strong className="block mb-2 text-primary">{data.subject}</strong>
                            <p>Accuracy: {data.accuracyPct}%</p>
                            <p>Attempts: {data.attempts}</p>
                            <p>XP Earned: {Math.round(data.xp || 0)}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="accuracyPct" radius={[0, 4, 4, 0]} barSize={32}>
                    {(data?.subject_breakdown || []).map((entry, index) => {
                      const colors = ["#0ea5e9", "#f59e0b", "#10b981", "#8b5cf6", "#ef4444"];
                      return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="panel">
            <h3>Top Students</h3>
            <div className="table-wrap">
              <table className="clean-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Attempts</th>
                    <th>Accuracy</th>
                    <th>XP</th>
                    <th>Level</th>
                    <th>Badges</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.student_progress || []).slice(0, 15).map((row) => (
                    <tr key={row.student_id}>
                      <td>{row.student_id}</td>
                      <td>{row.attempts}</td>
                      <td>{pct(row.accuracy)}%</td>
                      <td>{Math.round(row.xp || 0)}</td>
                      <td>Lv {row.level || 1}</td>
                      <td>{row.badges || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h3>Recent Activity</h3>
            <div className="recent-list">
              {(data?.recent_activity || []).slice(0, 24).map((row, idx) => (
                <div key={`${row.student_id}-${row.timestamp}-${idx}`} className="recent-row">
                  <div>
                    <strong>{row.student_id}</strong>
                    <small>
                      {row.school || "Unknown school"} | Grade {row.class_grade || "?"} | {row.subject || "Unknown"} | +{Number(row.xp_awarded || 0)} XP
                    </small>
                  </div>
                  <div className={`result-chip ${row.outcome ? "ok" : "bad"}`}>
                    {row.outcome ? "Correct" : "Incorrect"}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      ) : (
        <section className="panel">
          <h3>AI Question Generator</h3>
          <p className="muted">Generate NCERT-aligned questions for your students using Groq AI.</p>

          <div className="filter-grid mt-4">
            <label>
              Topic
              <input
                type="text"
                value={genTopic}
                onChange={(e) => setGenTopic(e.target.value)}
                placeholder="e.g. Addition, Fractions"
                className="text-input"
              />
            </label>
            <label>
              Subject
              <select value={genSubject} onChange={(e) => setGenSubject(e.target.value)} className="select-input">
                <option value="Mathematics">Maths</option>
                <option value="English">English</option>
                <option value="Science">Sciences</option>
              </select>
            </label>
            <label>
              Grade
              <select value={genGrade} onChange={(e) => setGenGrade(e.target.value)} className="select-input">
                {Array.from({ length: 12 }, (_, i) => i + 1).map(g => (
                  <option key={g} value={g}>Grade {g}</option>
                ))}
              </select>
            </label>
            <label>
              Count
              <input
                type="number"
                value={genCount}
                onChange={(e) => setGenCount(e.target.value)}
                className="text-input"
              />
            </label>
            <div className="flex items-end">
              <button
                className="btn-primary w-full"
                onClick={handleGenerate}
                disabled={genLoading || !genTopic}
              >
                {genLoading ? "Generating..." : "Generate with AI"}
              </button>
            </div>
          </div>

          {genQuestions.length > 0 && (
            <div className="mt-8">
              <h4>Review Generated Content</h4>
              <div className="recent-list">
                {genQuestions.map((q, idx) => (
                  <div key={idx} className="recent-row flex-col items-start gap-2">
                    <div className="flex justify-between w-full">
                      <strong>{q.question}</strong>
                      <span className="pill small">{q.difficulty}</span>
                    </div>
                    <div className="text-sm">Options: {q.options.join(", ")}</div>
                    <div className="text-sm font-bold text-teal-700">Answer: {q.answer}</div>
                  </div>
                ))}
              </div>
              <button className="btn-outline mt-4" onClick={() => toast.show("Ready to sync to database", "info")}>
                Approve and Add to Syllabus
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

