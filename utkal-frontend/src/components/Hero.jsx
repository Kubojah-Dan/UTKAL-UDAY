import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Hero() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const primaryAction = () => {
    if (!user) navigate("/login");
    else if (user.role === "teacher") navigate("/teacher");
    else navigate("/home");
  };

  return (
    <section className="hero">
      <div className="hero-content">
        <div className="hero-tag">Offline-first for Indian classrooms</div>
        <h1>Gamified Math, Science, and English learning for Rural Education</h1>
        <p>
          Adaptive quests, XP, levels, badges, local progress tracking, and teacher analytics in one platform.
          Built for browser and Play Store deployment with the same codebase.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={primaryAction}>
            {user ? "Open Dashboard" : "Login and Start"}
          </button>
          <button className="btn-outline" onClick={() => navigate("/download-app")}>
            Download App
          </button>
        </div>
        <div className="hero-chips">
          <span>Quizzes + Quests</span>
          <span>Role-based Login</span>
          <span>Adaptive Recommendations</span>
          <span>Teacher Analytics</span>
          <span>XP, Levels, Badges</span>
        </div>
      </div>
      <div className="hero-art">
        <div className="orb orb-one" />
        <div className="orb orb-two" />
        <img src="/utkal-uday-logo.svg" alt="Utkal Uday" />
      </div>
    </section>
  );
}
