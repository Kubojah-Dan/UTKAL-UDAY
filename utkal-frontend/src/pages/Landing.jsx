import React, { useEffect, useState } from "react";
import Hero from "../components/Hero";
import Features from "../components/Features";
import { fetchModelReadiness } from "../services/learning";

const OFFERINGS = [
  {
    title: "Personalized Learning Paths",
    desc: "Recommendations adapt to each learner's performance so practice time is focused on weak skills."
  },
  {
    title: "Teacher Monitoring by School/Class",
    desc: "Dashboards support grade and school filtering so teachers can track the exact students they teach."
  },
  {
    title: "Gamified Motivation",
    desc: "Students earn XP, climb levels, and unlock badges as they solve more questions correctly."
  },
  {
    title: "Offline-First Delivery",
    desc: "The app keeps working in low-connectivity areas and syncs progress when internet is restored."
  }
];

const IMPACT_STATS = [
  {
    value: "98.1%",
    title: "Rural children (age 6-14) enrolled",
    desc: "Still leaves about 1.9% out of school in this age band.",
    source: "ASER 2024 (rural survey)"
  },
  {
    value: "7.9%",
    title: "Rural teens (age 15-16) not enrolled",
    desc: "Drop-off rises in higher age groups, indicating retention challenges.",
    source: "ASER 2024 (rural survey)"
  },
  {
    value: "73.5%",
    title: "Rural population (age 5+) can use internet",
    desc: "Roughly 1 in 4 still lacks practical internet use capability.",
    source: "MOSPI NSO survey (Jan-Mar 2025)"
  },
  {
    value: "83.3%",
    title: "Rural households with internet at home",
    desc: "Coverage improved, but usage and learning quality gaps remain.",
    source: "MOSPI NSO survey (Jan-Mar 2025)"
  }
];

const BENEFITS = [
  "Improves foundational skills with frequent short practice loops.",
  "Gives teachers actionable mastery and engagement data every week.",
  "Supports blended learning where internet is intermittent.",
  "Creates student motivation through points, levels, and badges."
];

export default function Landing() {
  const [readiness, setReadiness] = useState(null);

  useEffect(() => {
    fetchModelReadiness()
      .then(setReadiness)
      .catch(() => setReadiness(null));
  }, []);

  return (
    <div className="container landing">
      <Hero />
      <Features />

      <section className="panel">
        <h2 className="section-title">What Utkal Uday Offers</h2>
        <div className="offer-grid">
          {OFFERINGS.map((item) => (
            <article key={item.title} className="offer-card">
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Rural Education Access Snapshot (India)</h2>
        <p className="muted">
          These indicators help explain why offline-first and teacher-guided digital learning still matters.
        </p>
        <div className="impact-grid">
          {IMPACT_STATS.map((stat) => (
            <article key={stat.title} className="impact-card">
              <strong>{stat.value}</strong>
              <h3>{stat.title}</h3>
              <p>{stat.desc}</p>
              <small>{stat.source}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Benefits for Schools</h2>
        <div className="benefit-list">
          {BENEFITS.map((item) => (
            <div key={item} className="benefit-item">
              <span className="dot" />
              <p>{item}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Model Readiness</h2>
        {!readiness && <p className="muted">Readiness status is unavailable while backend is offline.</p>}
        {readiness && (
          <>
            <div className="readiness-status">
              <span className="label">Current status</span>
              <strong>{readiness.status}</strong>
            </div>
            <div className="readiness-grid">
              <div>
                <span className="label">BKT skills</span>
                <strong>{readiness.bkt_skill_count}</strong>
              </div>
              <div>
                <span className="label">LSTM model</span>
                <strong>{readiness.has_temporal_lstm ? "Available" : "Missing"}</strong>
              </div>
              <div>
                <span className="label">Subjects in bank</span>
                <strong>{(readiness.question_bank_subjects || []).join(", ") || "None"}</strong>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
