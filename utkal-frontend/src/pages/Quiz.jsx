import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Clock, CheckCircle, XCircle } from 'lucide-react';

export default function Quiz() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getTranslatedContent } = useLanguage();
  
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
  }, [quizId]);

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
        api.get(`/questions/${id}`).catch(() => null)
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
      const isCorrect = userAnswer === q.answer;
      
      if (isCorrect) {
        correct++;
        earnedMarks += q.marks || 1;
      }
      totalMarks += q.marks || 1;
      
      return {
        question: q,
        userAnswer,
        isCorrect
      };
    });
    
    setResults({
      correct,
      total: questions.length,
      earnedMarks,
      totalMarks,
      percentage: Math.round((earnedMarks / totalMarks) * 100),
      details: questionResults
    });

    // Save attempt to backend
    try {
      // Save to MongoDB for analytics
      await api.post('/tools/save-quiz-attempt', {
        quiz_id: quizId,
        student_id: user.id,
        score: results.percentage,
        correct: results.correct,
        total: results.total,
        timestamp: new Date().toISOString(),
        answers: answers
      });
      
      // Also save interactions for progress tracking
      await api.post('/sync/interactions', {
        student_id: user.id,
        interactions: questions.map(q => ({
          student_id: user.id,
          interaction_id: `${user.id}-${q.id}-${Date.now()}`,
          quest_id: q.id,
          problem_id: q.id,
          timestamp: Date.now(),
          outcome: answers[q.id] === q.answer,
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
          xp_awarded: answers[q.id] === q.answer ? (q.marks || 1) * 10 : 0
        }))
      });
    } catch (err) {
      console.warn('Failed to sync quiz results:', err);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <div className="container"><div className="panel">Loading quiz...</div></div>;
  }

  if (!quiz || questions.length === 0) {
    return <div className="container"><div className="panel">Quiz not found or no questions available.</div></div>;
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
              <strong>{results.earnedMarks}/{results.totalMarks}</strong>
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
                    {!item.isCorrect && (
                      <p className="text-sm">Correct answer: <span className="text-green-700 font-bold">{item.question.answer}</span></p>
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
            <span className="pill">{currentQuestion.marks || 1} mark{(currentQuestion.marks || 1) > 1 ? 's' : ''}</span>
          </div>

          <h3 className="mb-4">{getTranslatedContent(currentQuestion, 'question')}</h3>

          {currentQuestion.type === 'mcq' || currentQuestion.type === 'image_mcq' ? (
            <div className="option-grid">
              {(currentQuestion.options || []).map((opt, idx) => (
                <label key={idx} className={`option ${answers[currentQuestion.id] === opt ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    value={opt}
                    checked={answers[currentQuestion.id] === opt}
                    onChange={(e) => handleAnswer(currentQuestion.id, e.target.value)}
                  />
                  <span>{getTranslatedContent({ ...currentQuestion, question: opt }, 'question')}</span>
                </label>
              ))}
            </div>
          ) : (
            <textarea
              value={answers[currentQuestion.id] || ''}
              onChange={(e) => handleAnswer(currentQuestion.id, e.target.value)}
              placeholder="Type your answer here..."
              className="text-input w-full h-32"
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
