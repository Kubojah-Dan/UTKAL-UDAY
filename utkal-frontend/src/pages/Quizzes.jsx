import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Clock, BookOpen } from 'lucide-react';

function quizExpiryLabel(quiz) {
  if (!quiz?.expires_at) return "Available now";
  const expires = new Date(quiz.expires_at);
  const diffMs = expires.getTime() - Date.now();
  if (diffMs <= 0) return "Expired";
  const diffHours = Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60)));
  if (diffHours < 24) return `Expires in ${diffHours}h`;
  return `Expires ${expires.toLocaleDateString()}`;
}

export default function Quizzes() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuizzes();
  }, [user.class_grade]);

  const loadQuizzes = async () => {
    try {
      const res = await api.get(`/tools/quizzes?grade=${user.class_grade}`);
      setQuizzes(res.data.quizzes || []);
    } catch (err) {
      console.error('Failed to load quizzes:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container"><div className="panel">Loading quizzes...</div></div>;
  }

  return (
    <div className="container">
      <section className="panel">
        <h2>Available Quizzes</h2>
        <p className="muted">Test your knowledge with timed assessments</p>

        {quizzes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">No active quizzes are available for Grade {user.class_grade} right now.</p>
            <p className="text-sm text-gray-500 mt-2">Quizzes now disappear after the 24-hour window closes or after you submit them.</p>
          </div>
        ) : (
          <div className="quest-grid">
            {quizzes.map((quiz) => (
              <article key={quiz.id} className="quest-card">
                <div className="pill-row">
                  <span className="pill with-icon"><BookOpen className="w-4 h-4" />{quiz.subject || "Quiz"}</span>
                  <span className="pill">Grade {quiz.grade}</span>
                </div>
                <h4>{quiz.title}</h4>
                <div className="flex items-center gap-4 text-sm text-gray-600 mt-2">
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {quiz.duration_minutes} min
                  </span>
                  <span>{quiz.question_ids?.length || 0} questions</span>
                </div>
                <p className="text-xs text-teal-700 font-semibold mt-3">{quizExpiryLabel(quiz)}</p>
                <button 
                  className="btn-primary small mt-4" 
                  onClick={() => navigate(`/quiz/${quiz.id}`)}
                >
                  Start Quiz
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
