import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { addInteraction, getInteractionsByStudent } from "../services/events";
import { fetchQuestion, fetchRecommendations } from "../services/learning";
import { syncData } from "../services/sync";
import { computeXpForAttempt, evaluateBadges } from "../services/gamification";
import { API_BASE } from "../services/api";
import { displayAnswer, evaluateQuestionAnswer, normalizeQuestionType } from "../services/questionUtils";
import SubjectIcon from "../components/SubjectIcon";
import { Sparkles } from "lucide-react";

function mediaUrl(path) {
  if (!path) return "";
  if (String(path).startsWith("http") || String(path).startsWith("data:")) return path;
  return `${API_BASE}${String(path).startsWith("/") ? "" : "/"}${path}`;
}

export default function Quest() {
  const { questId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getTranslatedContent, language } = useLanguage();
  const forceDynamicNextRef = useRef(false);

  const [question, setQuestion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [answer, setAnswer] = useState("");
  const [startTs, setStartTs] = useState(Date.now());
  const [hintsUsed, setHintsUsed] = useState(0);
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState("");
  const [showCelebration, setShowCelebration] = useState(false);
  const [timeLeft, setTimeLeft] = useState(null);
  const [timerActive, setTimerActive] = useState(false);
  const [questRefreshKey, setQuestRefreshKey] = useState(0);
  const recentQuestionIdsRef = useRef([]);

  const rememberQuestionId = (questionId) => {
    if (!questionId) return;
    const normalizedId = String(questionId);
    recentQuestionIdsRef.current = [
      normalizedId,
      ...recentQuestionIdsRef.current.filter((id) => id !== normalizedId),
    ].slice(0, 25);
  };

  // Timer based on difficulty
  useEffect(() => {
    if (!question) return;
    const seconds = question.difficulty === 'hard' ? 120 : question.difficulty === 'medium' ? 90 : 60;
    setTimeLeft(seconds);
    setTimerActive(true);
  }, [question]);

  useEffect(() => {
    if (!timerActive || timeLeft === null || feedback) return;
    if (timeLeft <= 0) { setTimerActive(false); return; }
    const t = setTimeout(() => setTimeLeft(v => v - 1), 1000);
    return () => clearTimeout(t);
  }, [timeLeft, timerActive, feedback]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setError("");
      setFeedback(null);
      setAnswer("");
      setHintsUsed(0);
      try {
        let id = forceDynamicNextRef.current ? null : questId;
        if (!id) {
          // Use dynamic quest generation endpoint (finds weakest topic)
          try {
            const { api: apiClient } = await import('../services/api');
            const params = new URLSearchParams();
            params.set("grade", String(user.class_grade || 5));
            params.set("language", language);
            params.set("request_ts", String(Date.now()));
            recentQuestionIdsRef.current.forEach((questionId) => {
              params.append("exclude_ids", questionId);
            });

            const dynRes = await apiClient.get(`/quests/next/${user.id}?${params.toString()}`);
            const dynQuestions = dynRes.data?.questions || [];
            if (dynQuestions.length > 0) {
              const firstQuestion = dynQuestions[0];
              if (!cancelled) {
                setQuestion(firstQuestion);
                rememberQuestionId(firstQuestion.id);
                setStartTs(Date.now());
                setLoading(false);
              }

              if (firstQuestion?.id) {
                void fetchQuestion(firstQuestion.id, { language })
                  .then((freshQuestion) => {
                    if (!cancelled && freshQuestion?.id === firstQuestion.id) {
                      setQuestion(freshQuestion);
                    }
                  })
                  .catch(() => null);
              }

              dynQuestions.slice(1, 3).forEach((nextQuestion) => {
                if (nextQuestion?.id) {
                  void fetchQuestion(nextQuestion.id, { language }).catch(() => null);
                }
              });
              return;
            }
          } catch (_) {}
          // Fallback to recommendations
          const rec = await fetchRecommendations(user.id, {
            limit: 5,
            grade: user.class_grade || undefined,
            excludeIds: recentQuestionIdsRef.current,
          });
          id = rec?.quests?.find((quest) => !recentQuestionIdsRef.current.includes(String(quest?.quest_id)))?.quest_id;
        }
        if (!id) {
          const { getLocalQuestions } = await import("../db/database");
          const localQuestions = await getLocalQuestions({
            grade: user.class_grade || undefined,
          });
          id = localQuestions.find((candidate) => {
            const candidateId = String(candidate?.id || "").trim();
            return candidateId && !recentQuestionIdsRef.current.includes(candidateId);
          })?.id;
        }
        if (!id) {
          throw new Error("No quest available");
        }
        const q = await fetchQuestion(id, { language });
        if (!cancelled) {
          setQuestion(q);
          rememberQuestionId(q?.id);
          setStartTs(Date.now());
        }
      } catch (err) {
        console.error(err);
        if (!cancelled) {
          setError("Unable to load quest. Please try again.");
        }
      } finally {
        forceDynamicNextRef.current = false;
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [questId, user.id, user.class_grade, questRefreshKey]);

  useEffect(() => {
    if (!question?.id || language === "en" || question.language_variants?.[language] || !navigator.onLine) {
      return undefined;
    }

    let cancelled = false;

    const refreshInBackground = async () => {
      for (const delayMs of [2500, 8000]) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        if (cancelled) return;

        try {
          const refreshed = await fetchQuestion(question.id, { language });
          if (cancelled || !refreshed) return;

          setQuestion((current) => current?.id === refreshed.id ? refreshed : current);
          if (refreshed.language_variants?.[language]) {
            return;
          }
        } catch (_) {
          return;
        }
      }
    };

    void refreshInBackground();

    return () => {
      cancelled = true;
    };
  }, [question?.id, language]);

  const submitAnswer = async () => {
    if (!question) return;
    setTimerActive(false);
    const evaluation = evaluateQuestionAnswer(question, answer);
    const effectiveCorrect = evaluation.requiresManualReview ? evaluation.score >= 0.5 : evaluation.correct;
    const answerPreview = displayAnswer(question);
    const xpAwarded = computeXpForAttempt({
      correct: effectiveCorrect,
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
      outcome: effectiveCorrect,
      time_ms: Date.now() - startTs,
      hints: hintsUsed,
      path_steps: 1,
      steps_json: "",
      xp_awarded: xpAwarded
    };

    await addInteraction(interaction);

    try {
      await syncData(user.id);
    } catch (err) {
      console.warn("Sync deferred", err);
    }

    const all = await getInteractionsByStudent(user.id);
    const game = evaluateBadges(all);

    setFeedback({
      ok: effectiveCorrect,
      xp: xpAwarded,
      level: game.level,
      text: evaluation.requiresManualReview
        ? "Answer submitted. This response is evaluated by key points."
        : effectiveCorrect
          ? "Correct answer. Great work."
          : `Not quite. Correct answer: ${answerPreview}`
    });

    // Update spaced repetition schedule
    try {
      const { api: apiClient } = await import('../services/api');
      await apiClient.post('/student/spaced-review/update', {
        student_id: user.id,
        question_id: question.id,
        correct: effectiveCorrect,
        time_ms: Date.now() - startTs,
        hints: hintsUsed
      });
    } catch (_) {}

    // Show celebration for correct answers with full XP
    if (effectiveCorrect && hintsUsed === 0) {
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 5000);
    }
  };

  if (loading) return <div className="container"><div className="panel">Loading quest...</div></div>;
  if (error) return <div className="container"><div className="panel error-text">{error}</div></div>;
  if (!question) return <div className="container"><div className="panel">No question found.</div></div>;

  const questionType = normalizeQuestionType(question.type, question.options);
  const translatedQuestion = getTranslatedContent(question, "question");
  const translatedPassage = getTranslatedContent(question, "passage");
  const translatedInstructions = getTranslatedContent(question, "instructions");
  const translatedOptions = question.language_variants?.[language]?.options || question.options || [];
  const translatedHint = getTranslatedContent(question, "hint");
  const fallbackHint = Array.isArray(question.hints) ? question.hints[0] : "";
  const hintToShow = translatedHint || question.hint || fallbackHint;

  return (
    <div className="container">
      <section className="panel question-panel">
        <div className="pill-row">
          <span className="pill with-icon"><SubjectIcon subject={question.subject} />{question.subject}</span>
          <span className="pill">Grade {question.grade}</span>
          <span className="pill">{question.skill_label}</span>
          {timeLeft !== null && !feedback && (
            <span className={`pill timer-pill ${timeLeft <= 15 ? 'timer-urgent' : ''}`}>
              {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
            </span>
          )}
        </div>
        {timeLeft !== null && !feedback && (
          <div className="timer-bar">
            <div
              className="timer-bar-fill"
              style={{
                width: `${(timeLeft / (question.difficulty === 'hard' ? 120 : question.difficulty === 'medium' ? 90 : 60)) * 100}%`,
                background: timeLeft <= 15 ? '#dc2626' : timeLeft <= 30 ? '#f59e0b' : '#0f766e'
              }}
            />
          </div>
        )}
        {translatedPassage && (
          <article className="passage-card">
            <p className="passage-label">Read the passage</p>
            <p className="passage-body" style={{ whiteSpace: "pre-wrap" }}>{translatedPassage}</p>
          </article>
        )}
        {translatedInstructions && (
          <p className="question-instructions" style={{ whiteSpace: "pre-wrap" }}>
            {translatedInstructions}
          </p>
        )}
        <h2 className="question-text" style={{ whiteSpace: "pre-wrap" }}>{translatedQuestion}</h2>

        {question.svg_markup && (
          <div className="svg-question-wrap" dangerouslySetInnerHTML={{ __html: question.svg_markup }} />
        )}

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

        {questionType === "mcq" || questionType === "image_mcq" ? (
          <div className="option-grid">
            {(question.options || []).map((opt, idx) => {
              const translatedOpt = translatedOptions[idx] || opt;
              return (
                <label key={`${idx}-${opt}`} className={`option ${answer === opt ? "selected" : ""}`}>
                  <input
                    type="radio"
                    name="question-option"
                    value={opt}
                    checked={answer === opt}
                    onChange={(e) => setAnswer(e.target.value)}
                  />
                  <span>{translatedOpt}</span>
                </label>
              );
            })}
          </div>
        ) : questionType === "descriptive" ? (
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Write your answer in detail"
            className="text-input w-full h-40"
          />
        ) : (
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder={questionType === "fill_blank" ? "Fill in the blank" : "Type your answer"}
            className="text-input"
          />
        )}

        <div className="question-actions">
          <button className="btn-primary" onClick={submitAnswer} disabled={!answer}>Submit</button>
          <button className="btn-outline" onClick={() => setHintsUsed((v) => v + 1)}>Use Hint ({hintsUsed})</button>
          <button className="btn-outline" onClick={() => navigate("/progress")}>Go to Progress</button>
        </div>

        {hintsUsed > 0 && hintToShow && (
          <div className="hint-box">
            <strong>Hint:</strong> {hintToShow}
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
            <button
              className="btn-outline small"
              onClick={() => {
                forceDynamicNextRef.current = true;
                setQuestRefreshKey((value) => value + 1);
              }}
            >
              Next Quest
            </button>
            <button className="btn-primary small" onClick={() => navigate("/progress")}>View Progress</button>
          </div>
        </div>
      )}

      {showCelebration && (
        <div className="celebration-overlay">
          <div className="celebration-content">
            <Sparkles className="celebration-icon" size={80} />
            <h2>🎉 Perfect!</h2>
            <p>Full XP Earned!</p>
          </div>
        </div>
      )}
    </div>
  );
}
