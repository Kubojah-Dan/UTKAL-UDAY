import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { addInteraction } from "../services/events";
import { fetchQuestion, fetchRecommendations } from "../services/learning";
import { pushInteractions } from "../services/sync";

function isCorrectAnswer(question, answer) {
  return String(answer).trim().toLowerCase() === String(question.answer || "").trim().toLowerCase();
}

export default function Quest() {
  const { questId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [question, setQuestion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [answer, setAnswer] = useState("");
  const [startTs, setStartTs] = useState(Date.now());
  const [hintsUsed, setHintsUsed] = useState(0);
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      setFeedback(null);
      try {
        let id = questId;
        if (!id) {
          const rec = await fetchRecommendations(user.id, { limit: 1 });
          id = rec?.quests?.[0]?.quest_id;
        }
        if (!id) {
          throw new Error("No quest available");
        }
        const q = await fetchQuestion(id);
        setQuestion(q);
        setStartTs(Date.now());
        setAnswer("");
        setHintsUsed(0);
      } catch (err) {
        console.error(err);
        setError("Unable to load quest. Please try again.");
      } finally {
        setLoading(false);
      }
    })();
  }, [questId, user.id]);

  const submitAnswer = async () => {
    if (!question) return;
    const correct = isCorrectAnswer(question, answer);
    const interaction = {
      student_id: user.id,
      interaction_id: `${user.id}-${Date.now()}`,
      quest_id: question.id,
      problem_id: question.id,
      subject: question.subject,
      grade: question.grade,
      skill_id: question.skill_id,
      timestamp: Date.now(),
      outcome: correct,
      time_ms: Date.now() - startTs,
      hints: hintsUsed,
      path_steps: 1,
      steps_json: ""
    };

    await addInteraction(interaction);

    try {
      await pushInteractions(user.id, [interaction]);
    } catch (err) {
      console.warn("Sync deferred", err);
    }

    setFeedback({
      ok: correct,
      text: correct ? "Correct answer. Great work." : `Not quite. Correct answer: ${question.answer}`
    });
  };

  if (loading) return <div className="container"><div className="panel">Loading quest...</div></div>;
  if (error) return <div className="container"><div className="panel error-text">{error}</div></div>;
  if (!question) return <div className="container"><div className="panel">No question found.</div></div>;

  return (
    <div className="container">
      <section className="panel question-panel">
        <div className="pill-row">
          <span className="pill">{question.subject}</span>
          <span className="pill">Grade {question.grade}</span>
          <span className="pill">{question.skill_label}</span>
        </div>
        <h2>{question.question}</h2>

        {question.type === "mcq" ? (
          <div className="option-grid">
            {(question.options || []).map((opt) => (
              <label key={opt} className={`option ${answer === opt ? "selected" : ""}`}>
                <input
                  type="radio"
                  name="question-option"
                  value={opt}
                  checked={answer === opt}
                  onChange={(e) => setAnswer(e.target.value)}
                />
                <span>{opt}</span>
              </label>
            ))}
          </div>
        ) : (
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer"
            className="text-input"
          />
        )}

        <div className="question-actions">
          <button className="btn-primary" onClick={submitAnswer} disabled={!answer}>Submit</button>
          <button className="btn-outline" onClick={() => setHintsUsed((v) => v + 1)}>Use Hint ({hintsUsed})</button>
          <button className="btn-outline" onClick={() => navigate("/progress")}>Go to Progress</button>
        </div>

        {hintsUsed > 0 && question.hint && (
          <div className="hint-box">
            <strong>Hint:</strong> {question.hint}
          </div>
        )}
      </section>

      {feedback && (
        <div className={`toast ${feedback.ok ? "success" : "warn"}`}>
          <p>{feedback.text}</p>
          <div className="toast-actions">
            <button className="btn-outline small" onClick={() => navigate("/quest")}>Next Quest</button>
            <button className="btn-primary small" onClick={() => navigate("/progress")}>View Progress</button>
          </div>
        </div>
      )}
    </div>
  );
}
