import React, { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
import { startAutoFlush } from "./services/offlineSync";
import { initBackgroundSync } from "./services/sync";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Quest from "./pages/Quest";
import Quiz from "./pages/Quiz";
import Quizzes from "./pages/Quizzes";
import SkillMap from "./pages/SkillMap";
import Progress from "./pages/Progress";
import TeacherDashboard from "./pages/TeacherDashboard";

function DashboardRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "teacher") return <Navigate to="/teacher" replace />;
  return <Navigate to="/home" replace />;
}

export default function App() {
  const { token, user } = useAuth();

  useEffect(() => {
    if (!token || !user || user.role !== "student") return undefined;

    // Initialize new background sync
    initBackgroundSync(user.id || user.student_id);

    return startAutoFlush(undefined, 45 * 1000);
  }, [token, user]);

  return (
    <LanguageProvider>
      <div className="app-shell">
        <Header />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />

          <Route
            path="/home"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quest"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Quest />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quest/:questId"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Quest />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quizzes"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Quizzes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quiz/:quizId"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Quiz />
              </ProtectedRoute>
            }
          />
          <Route
            path="/skill-map"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <SkillMap />
              </ProtectedRoute>
            }
          />
          <Route
            path="/progress"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <Progress />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher"
            element={
              <ProtectedRoute allowedRoles={["teacher"]}>
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/dashboard" element={<DashboardRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </LanguageProvider>
  );
}
