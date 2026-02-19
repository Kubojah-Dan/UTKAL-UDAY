import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
    >
      {label}
    </NavLink>
  );
}

export default function Header() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

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

        <nav className="nav">
          {!user && <NavItem to="/login" label="Login" />}
          {user?.role === "student" && (
            <>
              <NavItem to="/home" label="Home" />
              <NavItem to="/quest" label="Quest" />
              <NavItem to="/skill-map" label="Skills" />
              <NavItem to="/progress" label="Progress" />
            </>
          )}
          {user?.role === "teacher" && <NavItem to="/teacher" label="Teacher Dashboard" />}
        </nav>

        <div className="topbar-actions">
          {user ? (
            <>
              <span className="role-pill">{user.role}</span>
              <span className="user-name">{user.name}</span>
              <button className="btn-outline small" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <button className="btn-primary small" onClick={() => navigate("/login")}>Get Started</button>
          )}
        </div>
      </div>
    </header>
  );
}
