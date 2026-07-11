// Kali-web entrypoint. Bootstraps React, i18n, and mounts the app.
import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./lib/i18n";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <HashRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/session/:sid" element={<App />} />
        </Routes>
      </HashRouter>
    </ErrorBoundary>
  </React.StrictMode>
);