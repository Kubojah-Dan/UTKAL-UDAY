import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { api, API_BASE } from '../services/api';
import { defaultMarksForQuestion, displayAnswer, evaluateQuestionAnswer, normalizeQuestionType } from '../services/questionUtils';
import { Clock, CheckCircle, XCircle } from 'lucide-react';

function mediaUrl(path) {
  if (!path) return '';
  if (String(path).startsWith('http') || String(path).startsWith('data:')) return path;
  return `${API_BASE}${String(path).startsWith('/') ? '' : '/'}${path}`;
}

export default function Quiz() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getTranslatedContent, language } = useLanguage();
  
  const [quiz, setQuiz] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuiz();
  }, [quizId, language]);

  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0 || submitted) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, submitted]);

  const loadQuiz = async () => {
    try {
      const quizRes = await api.get(`/tools/quizzes?grade=${user.class_grade}`);
      const foundQuiz = quizRes.data.quizzes.find(q => q.id === quizId);
      
      if (!foundQuiz) {
        throw new Error('Quiz not found');
      }
      
      setQuiz(foundQuiz);
      
      // Load questions
      const questionPromises = foundQuiz.question_ids.map(id =>
        api.get(`/questions/${id}`, { params: { language } }).catch(() => null)
      );
      const questionResults = await Promise.all(questionPromises);
      const validQuestions = questionResults.filter(r => r?.data).map(r => r.data);
      
      setQuestions(validQuestions);
      setTimeLeft(foundQuiz.duration_minutes * 60);
    } catch (err) {
      console.error('Failed to load quiz:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    
    // Calculate results
    let correct = 0;
    let totalMarks = 0;
    let earnedMarks = 0;
    
    const questionResults = questions.map(q => {
      const userAnswer = answers[q.id];
      const evaluation = evaluateQuestionAnswer(q, userAnswer);
      const isCorrect = evaluation.requiresManualReview ? evaluation.score >= 0.5 : evaluation.correct;
      const marks = defaultMarksForQuestion(q);
      const scoredMarks = Math.round(marks * Math.max(0, Math.min(1, evaluation.score)) * 100) / 100;
      
      if (isCorrect) {
        correct++;
      }
      earnedMarks += scoredMarks;
      totalMarks += marks;
      
      return {
        question: q,
        userAnswer,
        isCorrect,
        score: evaluation.score,
        requiresManualReview: evaluation.requiresManualReview,
        scoredMarks,
        totalMarks: marks,
      };
    });
    
    const calculatedResults = {
      correct,
      total: questions.length,
      earnedMarks: Math.round(earnedMarks * 100) / 100,
      totalMarks,
      percentage: totalMarks > 0 ? Math.round((earnedMarks / totalMarks) * 100) : 0,
      details: questionResults
    };
    
    setResults(calculatedResults);

    // Save attempt to backend
    try {
      // Save to MongoDB for analytics
      await api.post('/tools/save-quiz-attempt', {
        quiz_id: quizId,
        student_id: user.id,
        score: calculatedResults.percentage,
        correct: calculatedResults.correct,
        total: calculatedResults.total,
        timestamp: new Date().toISOString(),
        answers: answers
      });
      
      // Also save interactions for progress tracking
      await api.post('/sync/interactions', {
        student_id: user.id,
        interactions: questionResults.map(item => {
          const q = item.question;
          return {
            student_id: user.id,
            interaction_id: `${user.id}-${q.id}-${Date.now()}`,
            quest_id: q.id,
            problem_id: q.id,
            timestamp: Date.now(),
            outcome: item.isCorrect,
            time_ms: Math.floor((quiz.duration_minutes * 60 - timeLeft) * 1000 / questions.length),
            subject: q.subject,
            grade: q.grade,
            school: user.school || null,
            class_grade: user.class_grade || null,
            skill_id: q.skill_id || 'quiz',
            difficulty: q.difficulty || 'medium',
            hints: 0,
            path_steps: 1,
            steps_json: '',
            xp_awarded: item.isCorrect ? defaultMarksForQuestion(q) * 10 : 0,
          };
        })
      });
    } catch (err) {
      console.error('Failed to sync quiz results:', err);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatMarks = (value) => {
    if (!Number.isFinite(Number(value))) return value;
    const num = Number(value);
    return Number.isInteger(num) ? num : num.toFixed(2);
  };

  if (loading) {
    return <div className="container"><div className="panel">Loading quiz...</div></div>;
  }

  if (!quiz || questions.length === 0) {
    return <div className="container"><div className="panel">Quiz not found, already attempted, expired, or no questions are available.</div></div>;
  }

  if (submitted && results) {
    return (
      <div className="container">
        <section className="panel">
          <h2>Quiz Results</h2>
          <div className="stats-grid mb-6">
            <div className="stat-card">
              <span>Score</span>
              <strong>{results.correct}/{results.total}</strong>
            </div>
            <div className="stat-card">
              <span>Marks</span>
              <strong>{formatMarks(results.earnedMarks)}/{formatMarks(results.totalMarks)}</strong>
            </div>
            <div className="stat-card">
              <span>Percentage</span>
              <strong>{results.percentage}%</strong>
            </div>
          </div>

          <h3 className="mb-4">Review Answers</h3>
          <div className="space-y-4">
            {results.details.map((item, idx) => (
              <div key={idx} className={`p-4 rounded-lg border-2 ${item.isCorrect ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
                <div className="flex items-start gap-3">
                  {item.isCorrect ? (
                    <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                  ) : (
                    <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
                  )}
                  <div className="flex-1">
                    <p className="font-semibold mb-2">Q{idx + 1}: {getTranslatedContent(item.question, 'question')}</p>
                    <p className="text-sm mb-1">Your answer: <span className={item.isCorrect ? 'text-green-700 font-bold' : 'text-red-700'}>{item.userAnswer || 'Not answered'}</span></p>
                    <p className="text-sm mb-1">Marks: <span className="font-semibold">{formatMarks(item.scoredMarks)}/{formatMarks(item.totalMarks)}</span></p>
                    {item.requiresManualReview && (
                      <p className="text-sm text-amber-700">Auto-evaluated by rubric. Teacher review recommended.</p>
                    )}
                    {!item.isCorrect && (
                      <p className="text-sm">Correct answer: <span className="text-green-700 font-bold">{displayAnswer(item.question)}</span></p>
                    )}
                    {item.question.explanation && (
                      <p className="text-sm mt-2 text-gray-600">{getTranslatedContent(item.question, 'explanation')}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex gap-4">
            <button className="btn-primary" onClick={() => navigate('/progress')}>View Progress</button>
            <button className="btn-outline" onClick={() => navigate('/home')}>Back to Home</button>
          </div>
        </section>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const currentType = normalizeQuestionType(currentQuestion.type, currentQuestion.options);
  const translatedPassage = getTranslatedContent(currentQuestion, 'passage');
  const translatedInstructions = getTranslatedContent(currentQuestion, 'instructions');
  const translatedOptions = currentQuestion.language_variants?.[language]?.options || currentQuestion.options || [];

  return (
    <div className="container">
      <section className="panel">
        <div className="flex justify-between items-center mb-6">
          <h2>{quiz.title}</h2>
          <div className="flex items-center gap-2 text-lg font-bold">
            <Clock className="w-5 h-5" />
            <span className={timeLeft < 60 ? 'text-red-600' : ''}>{formatTime(timeLeft)}</span>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentIndex + 1} of {questions.length}</span>
            <span>{Object.keys(answers).length} answered</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-teal-600 h-2 rounded-full transition-all"
              style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

        <div className="question-panel">
          <div className="pill-row mb-4">
            <span className="pill">{currentQuestion.subject}</span>
            <span className="pill">Grade {currentQuestion.grade}</span>
            <span className="pill">{defaultMarksForQuestion(currentQuestion)} mark{defaultMarksForQuestion(currentQuestion) > 1 ? 's' : ''}</span>
          </div>

          {translatedPassage && (
            <article className="passage-card mb-4">
              <p className="passage-label">Read the passage</p>
              <p className="passage-body" style={{ whiteSpace: 'pre-wrap' }}>{translatedPassage}</p>
            </article>
          )}
          {translatedInstructions && (
            <p className="question-instructions mb-3" style={{ whiteSpace: 'pre-wrap' }}>{translatedInstructions}</p>
          )}
          <h3 className="question-text mb-4" style={{ whiteSpace: 'pre-wrap' }}>{getTranslatedContent(currentQuestion, 'question')}</h3>
          {currentQuestion.svg_markup && (
            <div className="svg-question-wrap mb-4" dangerouslySetInnerHTML={{ __html: currentQuestion.svg_markup }} />
          )}
          {Array.isArray(currentQuestion.question_images) && currentQuestion.question_images.length > 0 && (
            <div className="question-media-grid">
              {currentQuestion.question_images.map((url, idx) => (
                <figure key={`quiz-qimg-${idx}`} className="media-card">
                  <img src={mediaUrl(url)} alt={`Question figure ${idx + 1}`} loading="lazy" />
                  <figcaption>Question image {idx + 1}</figcaption>
                </figure>
              ))}
            </div>
          )}

          {currentType === 'mcq' || currentType === 'image_mcq' ? (
            <div className="option-grid">
              {(currentQuestion.options || []).map((opt, idx) => {
                const translatedOpt = translatedOptions[idx] || opt;
                return (
                  <label key={idx} className={`option ${answers[currentQuestion.id] === opt ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      value={opt}
                      checked={answers[currentQuestion.id] === opt}
                      onChange={(e) => handleAnswer(currentQuestion.id, e.target.value)}
                    />
                    <span>{translatedOpt}</span>
                  </label>
                );
              })}
            </div>
          ) : currentType === 'descriptive' ? (
            <textarea
              value={answers[currentQuestion.id] || ''}
              onChange={(e) => handleAnswer(currentQuestion.id, e.target.value)}
              placeholder="Write your answer in detail..."
              className="text-input w-full h-40"
            />
          ) : (
            <input
              value={answers[currentQuestion.id] || ''}
              onChange={(e) => handleAnswer(currentQuestion.id, e.target.value)}
              placeholder={currentType === 'fill_blank' ? 'Fill in the blank' : 'Type your answer here...'}
              className="text-input w-full"
            />
          )}
        </div>

        <div className="flex justify-between mt-6">
          <button
            className="btn-outline"
            onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))}
            disabled={currentIndex === 0}
          >
            Previous
          </button>
          
          {currentIndex < questions.length - 1 ? (
            <button
              className="btn-primary"
              onClick={() => setCurrentIndex(prev => prev + 1)}
            >
              Next
            </button>
          ) : (
            <button
              className="btn-primary"
              onClick={handleSubmit}
            >
              Submit Quiz
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
