import React, { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LanguageSelector } from "../context/LanguageContext";
import { Menu, X } from "lucide-react";

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

export default function Header() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const onLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="topbar">
      <div className="container topbar-inner">
        <Link to="/" className="brand">
          <img src="/utkal-uday-logo.svg" alt="Utkal Uday" />
          <div>
            <strong>Utkal Uday</strong>
            <small>AI Learning Platform</small>
          </div>
        </Link>

        <button className="mobile-menu-btn" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <nav className={`nav ${menuOpen ? "" : "hidden"}`}>
          {!user && <NavItem to="/login" label="Login" />}
          {user?.role === "student" && (
            <>
              <NavItem to="/home" label="Home" />
              <NavItem to="/quest" label="Quest" />
              <NavItem to="/quizzes" label="Quizzes" />
              <NavItem to="/skill-map" label="Skills" />
              <NavItem to="/progress" label="Progress" />
            </>
          )}
          {user?.role === "teacher" && <NavItem to="/teacher" label="Teacher Dashboard" />}
        </nav>

        <div className={`topbar-actions ${menuOpen ? "" : "hidden"}`}>
          {user && <LanguageSelector />}
          {user ? (
            <>
              <span className="role-pill">{user.role}</span>
              {user.school && <span className="meta-pill">{user.school}</span>}
              {user.class_grade && <span className="meta-pill">Grade {user.class_grade}</span>}
              <span className="user-name">{user.name}</span>
              <button className="btn-outline small" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <button className="btn-primary small" onClick={() => navigate("/login")}>Get Started</button>
          )}
        </div>
      </div>

      {menuOpen && (
        <div className="mobile-menu">
          <nav className="mobile-nav">
            {!user && <NavItem to="/login" label="Login" onClick={() => setMenuOpen(false)} />}
            {user?.role === "student" && (
              <>
                <NavItem to="/home" label="Home" onClick={() => setMenuOpen(false)} />
                <NavItem to="/quest" label="Quest" onClick={() => setMenuOpen(false)} />
                <NavItem to="/quizzes" label="Quizzes" onClick={() => setMenuOpen(false)} />
                <NavItem to="/skill-map" label="Skills" onClick={() => setMenuOpen(false)} />
                <NavItem to="/progress" label="Progress" onClick={() => setMenuOpen(false)} />
              </>
            )}
            {user?.role === "teacher" && <NavItem to="/teacher" label="Teacher Dashboard" onClick={() => setMenuOpen(false)} />}
          </nav>

          <div className="mobile-actions">
            {user && (
              <div className="mobile-user-info">
                <span className="user-name">{user.name}</span>
                <span className="role-pill">{user.role}</span>
                {user.school && <span className="meta-pill">{user.school}</span>}
                {user.class_grade && <span className="meta-pill">Grade {user.class_grade}</span>}
              </div>
            )}
            {user && <LanguageSelector />}
            {user ? (
              <button className="btn-outline" style={{width: '100%', marginTop: '12px'}} onClick={() => { onLogout(); setMenuOpen(false); }}>Logout</button>
            ) : (
              <button className="btn-primary" style={{width: '100%', marginTop: '12px'}} onClick={() => { navigate("/login"); setMenuOpen(false); }}>Get Started</button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
