import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchQuestionList } from "../services/learning";
import { getBktParams } from "../services/pouch";
import { getAllInteractions } from "../services/events";

export default function SkillMap() {
  const [questions, setQuestions] = useState([]);
  const [bkt, setBkt] = useState({});
  const [interactions, setInteractions] = useState([]);

  useEffect(() => {
    (async () => {
      const [qRes, bktParams, ints] = await Promise.all([
        fetchQuestionList({ limit: 200 }),
        getBktParams(),
        getAllInteractions(5000)
      ]);
      setQuestions(qRes.questions || []);
      setBkt(bktParams || {});
      setInteractions(ints || []);
    })();
  }, []);

  const skillCards = useMemo(() => {
    const map = {};
    questions.forEach((q) => {
      const sid = String(q.skill_id || "unknown");
      map[sid] = map[sid] || {
        skill_id: sid,
        skill_label: q.skill_label || sid,
        subject: q.subject,
        grade: q.grade,
        questions: []
      };
      map[sid].questions.push(q);
    });

    const stats = {};
    interactions.forEach((it) => {
      const sid = String(it.skill_id || "unknown");
      stats[sid] = stats[sid] || { attempts: 0, correct: 0 };
      stats[sid].attempts += 1;
      stats[sid].correct += it.outcome ? 1 : 0;
    });

    return Object.values(map)
      .map((skill) => {
        const local = stats[skill.skill_id] || { attempts: 0, correct: 0 };
        const bktScore = bkt?.[skill.skill_id]?.p_init;
        const localScore = local.attempts > 0 ? local.correct / local.attempts : 0;
        const mastery = Math.round(((typeof bktScore === "number" ? bktScore : localScore) || 0) * 100);
        return { ...skill, attempts: local.attempts, mastery };
      })
      .sort((a, b) => b.mastery - a.mastery);
  }, [questions, interactions, bkt]);

  return (
    <div className="container">
      <section className="panel">
        <h2>Skill Map</h2>
        <p className="muted">Track mastery by skill, subject, and grade.</p>
        <div className="skill-grid">
          {skillCards.map((skill) => (
            <article key={skill.skill_id} className="skill-card">
              <div className="pill-row">
                <span className="pill">{skill.subject}</span>
                <span className="pill">Grade {skill.grade}</span>
              </div>
              <h3>{skill.skill_label}</h3>
              <div className="mastery-row">
                <span>Mastery</span>
                <strong>{skill.mastery}%</strong>
              </div>
              <div className="meter">
                <span style={{ width: `${Math.max(5, skill.mastery)}%` }} />
              </div>
              <p className="muted">Attempts: {skill.attempts}</p>

              <div className="skill-links">
                {skill.questions.slice(0, 3).map((q) => (
                  <Link key={q.id} to={`/quest/${q.id}`}>
                    {q.id}
                  </Link>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
