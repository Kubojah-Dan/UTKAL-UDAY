import React, { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
import { useToast } from "./context/ToastContext";
import { startAutoFlush } from "./services/offlineSync";
import { initBackgroundSync } from "./services/sync";
import { api } from "./services/api";
import { getSeenNotifications, markNotificationsSeen, showBrowserNotification } from "./services/notifications";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Quest from "./pages/Quest";
import Quiz from "./pages/Quiz";
import Quizzes from "./pages/Quizzes";
import SkillMap from "./pages/SkillMap";
import Progress from "./pages/Progress";
import TeacherDashboard from "./pages/TeacherDashboard";
import InfoPage from "./pages/InfoPage";
import DownloadApp from "./pages/DownloadApp";

function DashboardRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "teacher") return <Navigate to="/teacher" replace />;
  return <Navigate to="/home" replace />;
}

export default function App() {
  const { token, user } = useAuth();
  const { showToast } = useToast();

  useEffect(() => {
    if (!token || !user || user.role !== "student") return undefined;

    // Initialize new background sync
    initBackgroundSync(user.id || user.student_id);

    return startAutoFlush(undefined, 45 * 1000);
  }, [token, user]);

  useEffect(() => {
    if (!token || !user || user.role !== "student") return undefined;

    let cancelled = false;

    const pollNotifications = async () => {
      try {
        const res = await api.get("/tools/notifications");
        if (cancelled) return;

        const notifications = res.data?.notifications || [];
        const seen = getSeenNotifications();
        const fresh = notifications.filter((item) => item?.id && !seen.has(String(item.id)));
        if (!fresh.length) return;

        fresh.slice(0, 3).forEach((item) => {
          showToast(`${item.title}: ${item.message}`, "info", 6500);
          showBrowserNotification(item);
        });
        markNotificationsSeen(fresh.map((item) => item.id));
      } catch (err) {
        console.warn("Notification poll failed", err);
      }
    };

    void pollNotifications();
    const intervalId = window.setInterval(pollNotifications, 60_000);
    window.addEventListener("focus", pollNotifications);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      window.removeEventListener("focus", pollNotifications);
    };
  }, [token, user, showToast]);

  return (
    <LanguageProvider>
      <div className="app-shell">
        <Header />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/features" element={<InfoPage pageKey="features" />} />
          <Route path="/schools-districts" element={<InfoPage pageKey="schools-districts" />} />
          <Route path="/offline-sync-guide" element={<InfoPage pageKey="offline-sync-guide" />} />
          <Route path="/about" element={<InfoPage pageKey="about" />} />
          <Route path="/blog-case-studies" element={<InfoPage pageKey="blog-case-studies" />} />
          <Route path="/help-center" element={<InfoPage pageKey="help-center" />} />
          <Route path="/pedagogy-research" element={<InfoPage pageKey="pedagogy-research" />} />
          <Route path="/privacy-policy" element={<InfoPage pageKey="privacy-policy" />} />
          <Route path="/terms-of-service" element={<InfoPage pageKey="terms-of-service" />} />
          <Route path="/contact" element={<InfoPage pageKey="contact" />} />
          <Route path="/download-app" element={<DownloadApp />} />

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
