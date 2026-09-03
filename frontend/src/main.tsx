import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { I18nProvider } from "./i18n";
import { applyInitialTheme, ThemeProvider } from "./theme/ThemeProvider";
import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";
import "./styles.css";
import "./phase3.css";
import "./phase4.css";
import "./ai-agent.css";
import "./ai-workspace.css";

// Apply the persisted/system theme before the first render so the initial
// paint is already dark when the user prefers (or has chosen) dark mode.
applyInitialTheme();

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Missing #root element in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <I18nProvider>
          <App />
        </I18nProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </StrictMode>,
);
