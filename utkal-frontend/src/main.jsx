import React from "react";

import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { registerSW } from "./sw/registerServiceWorker";
import { AuthProvider } from "./context/AuthContext";

// DB auto-initializes when pouch.js loads
// No initPouch needed anymore

registerSW();

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);
