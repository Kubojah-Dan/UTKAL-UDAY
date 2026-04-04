import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginUser, registerUser } from "../services/auth";
import { API_BASE } from "../services/api";
import { BookOpen, GraduationCap, Eye, EyeOff } from "lucide-react";

const GRADES = Array.from({ length: 12 }, (_, i) => i + 1);

function PasswordInput({ value, onChange, placeholder, required }) {
  const [show, setShow] = useState(false);
  return (
    <div className="auth-input-wrap">
      <input
        type={show ? "text" : "password"}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className="auth-input"
      />
      <button type="button" className="auth-eye" onClick={() => setShow(v => !v)} tabIndex={-1}>
        {show ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}

function describeAuthError(err, fallbackMessage) {
  const detail = err?.response?.data?.detail;
  if (detail) return detail;

  if (err?.code === "ERR_NETWORK" || !err?.response) {
    return `Cannot reach backend at ${API_BASE}. On a real phone, run the backend with --host 0.0.0.0 and point VITE_ANDROID_API_BASE to your computer's LAN IP.`;
  }

  return fallbackMessage;
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // panel-active = show register panel
  const initialActive = location.state?.mode === "register";
  const [panelActive, setPanelActive] = useState(initialActive);

  // Login state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Register state
  const [regRole, setRegRole] = useState("student");
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regSchool, setRegSchool] = useState("");
  const [regGrade, setRegGrade] = useState("5");
  const [regStudentId, setRegStudentId] = useState("");
  const [regTeacherCode, setRegTeacherCode] = useState("");
  const [regError, setRegError] = useState("");
  const [regLoading, setRegLoading] = useState(false);

  const redirect = location.state?.from;

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    setLoginLoading(true);
    try {
      const payload = await loginUser({ email: loginEmail, password: loginPassword });
      login(payload);
      navigate(redirect || (payload.user.role === "teacher" ? "/teacher" : "/home"), { replace: true });
    } catch (err) {
      setLoginError(describeAuthError(err, "Invalid email or password"));
    } finally {
      setLoginLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegError("");
    setRegLoading(true);
    try {
      const payload = await registerUser({
        role: regRole,
        name: regName,
        email: regEmail,
        password: regPassword,
        school: regSchool,
        classGrade: regGrade,
        studentId: regStudentId || undefined,
        teacherCode: regRole === "teacher" ? regTeacherCode : undefined,
      });
      login(payload);
      navigate(redirect || (payload.user.role === "teacher" ? "/teacher" : "/home"), { replace: true });
    } catch (err) {
      setRegError(describeAuthError(err, "Registration failed. Please try again."));
    } finally {
      setRegLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className={`auth-wrapper ${panelActive ? "panel-active" : ""}`}>

        {/* ── Register Form ── */}
        <div className="auth-form-box register-form-box">
          <form onSubmit={handleRegister}>
            <div className="auth-form-logo">
              <BookOpen size={28} />
              <span>Utkal Uday</span>
            </div>
            <h1>Create Account</h1>

            {/* Role toggle */}
            <div className="auth-role-toggle">
              <button
                type="button"
                className={`auth-role-btn ${regRole === "student" ? "active" : ""}`}
                onClick={() => setRegRole("student")}
              >
                <GraduationCap size={16} /> Student
              </button>
              <button
                type="button"
                className={`auth-role-btn ${regRole === "teacher" ? "active" : ""}`}
                onClick={() => setRegRole("teacher")}
              >
                <BookOpen size={16} /> Teacher
              </button>
            </div>

            <input className="auth-input" type="text" placeholder="Full Name" required value={regName} onChange={e => setRegName(e.target.value)} />
            <input className="auth-input" type="email" placeholder="Email Address" required value={regEmail} onChange={e => setRegEmail(e.target.value)} />
            <PasswordInput value={regPassword} onChange={e => setRegPassword(e.target.value)} placeholder="Password (min 6 chars)" required />
            <input className="auth-input" type="text" placeholder="School Name" required value={regSchool} onChange={e => setRegSchool(e.target.value)} />

            <select className="auth-input auth-select" value={regGrade} onChange={e => setRegGrade(e.target.value)} required>
              {GRADES.map(g => <option key={g} value={g}>Grade {g}</option>)}
            </select>

            {regRole === "student" && (
              <input className="auth-input" type="text" placeholder="Student ID (optional)" value={regStudentId} onChange={e => setRegStudentId(e.target.value)} />
            )}

            {regRole === "teacher" && (
              <PasswordInput value={regTeacherCode} onChange={e => setRegTeacherCode(e.target.value)} placeholder="Teacher Registration Code" required />
            )}

            {regError && <p className="auth-error">{regError}</p>}

            <button className="auth-submit-btn" type="submit" disabled={regLoading}>
              {regLoading ? "Creating account..." : "Sign Up"}
            </button>

            <div className="mobile-switch">
              <p>Already have an account?</p>
              <button type="button" className="mobile-switch-btn" onClick={() => setPanelActive(false)}>Sign In</button>
            </div>
          </form>
        </div>

        {/* ── Login Form ── */}
        <div className="auth-form-box login-form-box">
          <form onSubmit={handleLogin}>
            <div className="auth-form-logo">
              <BookOpen size={28} />
              <span>Utkal Uday</span>
            </div>
            <h1>Sign In</h1>
            <p className="auth-subtitle">Welcome back! Continue your learning journey.</p>

            <input className="auth-input" type="email" placeholder="Email Address" required value={loginEmail} onChange={e => setLoginEmail(e.target.value)} />
            <PasswordInput value={loginPassword} onChange={e => setLoginPassword(e.target.value)} placeholder="Password" required />

            {loginError && <p className="auth-error">{loginError}</p>}

            <button className="auth-submit-btn" type="submit" disabled={loginLoading}>
              {loginLoading ? "Signing in..." : "Sign In"}
            </button>

            <div className="mobile-switch">
              <p>Don't have an account?</p>
              <button type="button" className="mobile-switch-btn" onClick={() => setPanelActive(true)}>Sign Up</button>
            </div>
          </form>
        </div>

        {/* ── Sliding Overlay Panel ── */}
        <div className="slide-panel-wrapper">
          <div className="slide-panel">
            {/* Left content — visible when panel-active (register mode), prompts to switch to Sign In */}
            <div className="panel-content panel-content-left">
              <BookOpen size={48} style={{ marginBottom: 16, opacity: 0.9 }} />
              <h1>Welcome Back!</h1>
              <p>Already have an account? Sign in and continue your learning journey with Utkal Uday.</p>
              <button className="transparent-btn" onClick={() => setPanelActive(false)}>Sign In</button>
            </div>
            {/* Right content — visible by default (login mode), prompts to Sign Up */}
            <div className="panel-content panel-content-right">
              <GraduationCap size={48} style={{ marginBottom: 16, opacity: 0.9 }} />
              <h1>Hey There!</h1>
              <p>Begin your amazing learning journey by creating an account with Utkal Uday today.</p>
              <button className="transparent-btn" onClick={() => setPanelActive(true)}>Sign Up</button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
