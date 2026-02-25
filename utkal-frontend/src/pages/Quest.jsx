import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { addInteraction, getInteractionsByStudent } from "../services/events";
import { fetchQuestion, fetchRecommendations } from "../services/learning";
import { pushInteractions } from "../services/sync";
import { computeXpForAttempt, evaluateBadges } from "../services/gamification";
import { API_BASE } from "../services/api";
import SubjectIcon from "../components/SubjectIcon";

function normalizeAnswer(value) {
  return String(value || "")
    .replace(/\$\$/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function isCorrectAnswer(question, answer) {
  const normalized = normalizeAnswer(answer);
  const accepted = Array.isArray(question.accepted_answers) && question.accepted_answers.length > 0
    ? question.accepted_answers
    : [question.answer];
  return accepted.some((item) => normalizeAnswer(item) === normalized);
}

function mediaUrl(path) {
  if (!path) return "";
  if (String(path).startsWith("http")) return path;
  return `${API_BASE}${String(path).startsWith("/") ? "" : "/"}${path}`;
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
          const rec = await fetchRecommendations(user.id, { limit: 1, grade: user.class_grade || undefined });
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
  }, [questId, user.id, user.class_grade]);

  const submitAnswer = async () => {
    if (!question) return;
    const correct = isCorrectAnswer(question, answer);
    const xpAwarded = computeXpForAttempt({
      correct,
      difficulty: question.difficulty,
      hintsUsed
    });
    const interaction = {
      student_id: user.id,
      interaction_id: `${user.id}-${Date.now()}`,
      quest_id: question.id,
      problem_id: question.id,
      subject: question.subject,
      grade: question.grade,
      school: user.school || null,
      class_grade: user.class_grade || null,
      skill_id: question.skill_id,
      difficulty: question.difficulty,
      timestamp: Date.now(),
      outcome: correct,
      time_ms: Date.now() - startTs,
      hints: hintsUsed,
      path_steps: 1,
      steps_json: "",
      xp_awarded: xpAwarded
    };

    await addInteraction(interaction);

    try {
      await pushInteractions(user.id, [interaction]);
    } catch (err) {
      console.warn("Sync deferred", err);
    }

    const all = await getInteractionsByStudent(user.id);
    const game = evaluateBadges(all);

    setFeedback({
      ok: correct,
      xp: xpAwarded,
      level: game.level,
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
          <span className="pill with-icon"><SubjectIcon subject={question.subject} />{question.subject}</span>
          <span className="pill">Grade {question.grade}</span>
          <span className="pill">{question.skill_label}</span>
        </div>
        <h2 style={{ whiteSpace: "pre-line" }}>{question.question}</h2>

        {Array.isArray(question.question_images) && question.question_images.length > 0 && (
          <div className="question-media-grid">
            {question.question_images.map((url, idx) => (
              <figure key={`qimg-${idx}`} className="media-card">
                <img src={mediaUrl(url)} alt={`Question figure ${idx + 1}`} loading="lazy" />
                <figcaption>Question image {idx + 1}</figcaption>
              </figure>
            ))}
          </div>
        )}

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

        {hintsUsed > 0 && Array.isArray(question.analysis_images) && question.analysis_images.length > 0 && (
          <div className="question-media-grid">
            {question.analysis_images.map((url, idx) => (
              <figure key={`aimg-${idx}`} className="media-card">
                <img src={mediaUrl(url)} alt={`Analysis figure ${idx + 1}`} loading="lazy" />
                <figcaption>Analysis image {idx + 1}</figcaption>
              </figure>
            ))}
          </div>
        )}
      </section>

      {feedback && (
        <div className={`toast ${feedback.ok ? "success" : "warn"}`}>
          <p>{feedback.text}</p>
          <p className="xp-note">+{feedback.xp} XP earned | Level {feedback.level}</p>
          <div className="toast-actions">
            <button className="btn-outline small" onClick={() => navigate("/quest")}>Next Quest</button>
            <button className="btn-primary small" onClick={() => navigate("/progress")}>View Progress</button>
          </div>
        </div>
      )}
    </div>
  );
}
