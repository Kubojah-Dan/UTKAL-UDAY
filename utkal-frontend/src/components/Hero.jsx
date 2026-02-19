import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Hero() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [installEvent, setInstallEvent] = useState(null);

  useEffect(() => {
    const handler = (evt) => {
      evt.preventDefault();
      setInstallEvent(evt);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const installApp = async () => {
    if (!installEvent) return;
    installEvent.prompt();
    await installEvent.userChoice;
    setInstallEvent(null);
  };

  const primaryAction = () => {
    if (!user) navigate("/login");
    else if (user.role === "teacher") navigate("/teacher");
    else navigate("/home");
  };

  return (
    <section className="hero">
      <div className="hero-content">
        <div className="hero-tag">Offline-first for Indian classrooms</div>
        <h1>Gamified Math and Science learning for Grades 1-6</h1>
        <p>
          Adaptive quests, local progress tracking, and teacher analytics in one platform.
          Built for browser and Play Store deployment with the same codebase.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={primaryAction}>
            {user ? "Open Dashboard" : "Login and Start"}
          </button>
          <button className="btn-outline" onClick={installApp} disabled={!installEvent}>
            Install App
          </button>
        </div>
        <div className="hero-chips">
          <span>PWA + Capacitor</span>
          <span>Role-based Login</span>
          <span>Adaptive Recommendations</span>
          <span>Teacher Analytics</span>
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
