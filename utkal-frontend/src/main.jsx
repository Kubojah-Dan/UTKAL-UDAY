import React from "react";

import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { registerSW } from "./sw/registerServiceWorker";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { startAutoFlush } from "./services/offlineSync";

registerSW();
startAutoFlush(60_000);

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  </React.StrictMode>
);
