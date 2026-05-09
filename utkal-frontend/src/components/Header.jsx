import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LanguageSelector } from "../context/LanguageContext";
import { Menu, X, Wifi, WifiOff, RefreshCw, AlertCircle } from "lucide-react";
import { useSyncQueueStatus } from "../hooks/useSyncStatus";

function NavItem({ to, label, onClick }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
    >
      {label}
    </NavLink>
  );
}

/** Small pill in the header showing sync/connectivity status */
function SyncStatusPill() {
  const { pendingCount, failedCount, isOnline, isSyncing, manualSync } = useSyncQueueStatus();

  let status = "synced";
  if (!isOnline) status = "offline";
  else if (isSyncing) status = "syncing";
  else if (failedCount > 0) status = "failed";
  else if (pendingCount > 0) status = "pending";

  const labels = {
    synced:  "Online",
    offline: `Offline${pendingCount > 0 ? ` · ${pendingCount}` : ""}`,
    syncing: "Syncing…",
    pending: `${pendingCount} pending`,
    failed:  `${failedCount} failed`,
  };

  const titles = {
    synced:  "All data synced",
    offline: `You're offline. ${pendingCount} answer${pendingCount !== 1 ? "s" : ""} will sync when connected.`,
    syncing: "Syncing your data to the server…",
    pending: `${pendingCount} answer${pendingCount !== 1 ? "s" : ""} waiting to sync`,
    failed:  `${failedCount} item${failedCount !== 1 ? "s" : ""} failed to sync. Tap to retry.`,
  };

  const canRetry = isOnline && (status === "pending" || status === "failed");

  return (
    <button
      className={`sync-pill sync-pill--${status}`}
      title={titles[status]}
      onClick={canRetry ? manualSync : undefined}
      aria-label={titles[status]}
      disabled={isSyncing}
    >
      <span className="sync-pill-dot" aria-hidden="true" />
      {status === "syncing" ? (
        <RefreshCw size={11} className="spinning" aria-hidden="true" />
      ) : status === "offline" ? (
        <WifiOff size={11} aria-hidden="true" />
      ) : status === "failed" ? (
        <AlertCircle size={11} aria-hidden="true" />
      ) : status === "pending" ? (
        <RefreshCw size={11} aria-hidden="true" />
      ) : (
        <Wifi size={11} aria-hidden="true" />
      )}
      <span className="sync-pill-label">{labels[status]}</span>
    </button>
  );
}

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [topbarHeight, setTopbarHeight] = useState(0);
  const headerRef = useRef(null);

  const onLogout = () => {
    logout();
    navigate("/login");
  };

  useEffect(() => {
    const syncHeaderLayout = () => {
      const nextHeight = headerRef.current?.getBoundingClientRect().height ?? 0;
      setTopbarHeight(nextHeight);
      if (window.innerWidth > 768) setMenuOpen(false);
    };
    syncHeaderLayout();
    window.addEventListener("resize", syncHeaderLayout);
    return () => window.removeEventListener("resize", syncHeaderLayout);
  }, []);

  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  useEffect(() => {
    if (window.innerWidth > 768) return undefined;
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  return (
    <header className="topbar" ref={headerRef}>
      <div className="container topbar-inner">
        <Link to="/" className="brand">
          <img src="/utkal-uday-logo.svg" alt="Utkal Uday" />
          <div>
            <strong>Utkal Uday</strong>
            <small>AI Learning Platform</small>
          </div>
        </Link>

        <button
          className="mobile-menu-btn"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <nav className="nav desktop-nav">
          {user?.role === "student" && (
            <>
              <NavItem to="/home"     label="Home"    />
              <NavItem to="/quest"    label="Quest"   />
              <NavItem to="/quizzes"  label="Quizzes" />
              <NavItem to="/notes"    label="Notes"   />
              <NavItem to="/skill-map" label="Skills" />
              <NavItem to="/progress" label="Progress"/>
              <NavItem to="/leaderboard" label="Leaderboard" />
            </>
          )}
          {user?.role === "teacher" && <NavItem to="/teacher" label="Teacher Dashboard" />}
        </nav>

        <div className="topbar-actions desktop-actions">
          {/* Sync status pill — visible for logged-in students */}
          {user?.role === "student" && <SyncStatusPill />}
          {user && <LanguageSelector />}
          {user ? (
            <>
              <span className="role-pill">{user.role}</span>
              {user.class_grade && <span className="meta-pill">Grade {user.class_grade}</span>}
              <span className="user-name">{user.name}</span>
              <button className="btn-outline small" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <>
              <button className="btn-primary small" onClick={() => navigate("/login", { state: { mode: "register" } })}>Get Started</button>
              <button className="btn-outline small" onClick={() => navigate("/login")}>Login</button>
            </>
          )}
        </div>
      </div>

      {menuOpen && (
        <div
          className="mobile-menu"
          id="mobile-menu"
          style={{ top: `${topbarHeight}px`, height: `calc(100dvh - ${topbarHeight}px)` }}
        >
          <nav className="mobile-nav">
            {!user && <NavItem to="/login" label="Login" onClick={() => setMenuOpen(false)} />}
            {user?.role === "student" && (
              <>
                <NavItem to="/home"        label="Home"         onClick={() => setMenuOpen(false)} />
                <NavItem to="/quest"       label="Quest"        onClick={() => setMenuOpen(false)} />
                <NavItem to="/quizzes"     label="Quizzes"      onClick={() => setMenuOpen(false)} />
                <NavItem to="/notes"       label="Notes"        onClick={() => setMenuOpen(false)} />
                <NavItem to="/skill-map"   label="Skills"       onClick={() => setMenuOpen(false)} />
                <NavItem to="/progress"    label="Progress"     onClick={() => setMenuOpen(false)} />
                <NavItem to="/leaderboard" label="Leaderboard"  onClick={() => setMenuOpen(false)} />
              </>
            )}
            {user?.role === "teacher" && <NavItem to="/teacher" label="Teacher Dashboard" onClick={() => setMenuOpen(false)} />}
          </nav>

          <div className="mobile-actions">
            {user?.role === "student" && (
              <div style={{ marginBottom: 8 }}>
                <SyncStatusPill />
              </div>
            )}
            {user && (
              <div className="mobile-user-info">
                <span className="user-name">{user.name}</span>
                <span className="role-pill">{user.role}</span>
                {user.school    && <span className="meta-pill">{user.school}</span>}
                {user.class_grade && <span className="meta-pill">Grade {user.class_grade}</span>}
              </div>
            )}
            {user && <LanguageSelector />}
            {user ? (
              <button className="btn-outline" style={{width: "100%", marginTop: "12px"}} onClick={() => { onLogout(); setMenuOpen(false); }}>Logout</button>
            ) : (
              <button className="btn-primary" style={{width: "100%", marginTop: "12px"}} onClick={() => { navigate("/login", { state: { mode: "register" } }); setMenuOpen(false); }}>Get Started</button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
