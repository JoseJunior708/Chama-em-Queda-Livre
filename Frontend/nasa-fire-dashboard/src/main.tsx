import React from "react";
import ReactDOM from "react-dom/client";

import "@fontsource/ibm-plex-sans/latin-400.css";
import "@fontsource/ibm-plex-sans/latin-500.css";
import "@fontsource/ibm-plex-sans/latin-600.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "@fontsource/ibm-plex-mono/latin-500.css";
import "./index.css";

import App from "./App";

// Aplica o tema guardado antes do primeiro render, para não haver clarão.
try {
  const tema = window.localStorage.getItem("cql-tema");
  if (tema === "claro" || tema === "escuro") {
    document.documentElement.dataset.tema = tema;
  }
} catch {
  // Sem armazenamento, o tema segue a preferência do sistema.
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
