import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ allowedRoles, children }) {
  const { loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="container"><div className="panel">Loading session...</div></div>;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    if (user.role === "teacher") return <Navigate to="/teacher" replace />;
    return <Navigate to="/home" replace />;
  }

  return children;
}
