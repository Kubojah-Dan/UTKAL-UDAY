import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginUser } from "../services/auth";

const GRADE_OPTIONS = Array.from({ length: 12 }, (_, idx) => idx + 1);

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [role, setRole] = useState("student");
  const [name, setName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [school, setSchool] = useState("");
  const [classGrade, setClassGrade] = useState("5");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = await loginUser({ role, name, studentId, password, school, classGrade });
      login(payload);

      const redirect = location.state?.from;
      if (redirect) navigate(redirect, { replace: true });
      else navigate(payload.user.role === "teacher" ? "/teacher" : "/home", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container auth-wrap">
      <section className="panel auth-panel">
        <h2>Login to Utkal Uday</h2>
        <p className="muted">Choose student or teacher access.</p>

        <div className="role-toggle">
          <button
            type="button"
            className={role === "student" ? "active" : ""}
            onClick={() => setRole("student")}
          >
            Student
          </button>
          <button
            type="button"
            className={role === "teacher" ? "active" : ""}
            onClick={() => setRole("teacher")}
          >
            Teacher
          </button>
        </div>

        <form onSubmit={onSubmit} className="form-grid">
          <label>
            Name
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your full name"
            />
          </label>

          {role === "student" && (
            <label>
              Student ID (optional)
              <input
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                placeholder="e.g. G5-ROLL-12"
              />
            </label>
          )}

          <label>
            School
            <input
              required
              value={school}
              onChange={(e) => setSchool(e.target.value)}
              placeholder="Enter your school name"
            />
          </label>

          <label>
            Class Grade
            <select
              required
              value={classGrade}
              onChange={(e) => setClassGrade(e.target.value)}
              className="select-input"
            >
              {GRADE_OPTIONS.map((grade) => (
                <option key={grade} value={grade}>
                  Grade {grade}
                </option>
              ))}
            </select>
          </label>

          {role === "teacher" && (
            <label>
              Teacher Password
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter teacher password"
              />
            </label>
          )}

          {error && <div className="error-text">{error}</div>}

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </section>
    </div>
  );
}
