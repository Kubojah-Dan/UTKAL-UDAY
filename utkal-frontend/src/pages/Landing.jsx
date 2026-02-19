import React, { useEffect, useState } from "react";
import Hero from "../components/Hero";
import Features from "../components/Features";
import { fetchModelReadiness } from "../services/learning";

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
