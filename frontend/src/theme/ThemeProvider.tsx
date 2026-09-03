import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "forgeflow.theme";
const LEGACY_STORAGE_KEY = "team-project.theme";

function readStoredTheme(): Theme | null {
  try {
    const stored =
      window.localStorage.getItem(STORAGE_KEY) ?? window.localStorage.getItem(LEGACY_STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // localStorage unavailable (e.g. tests) — ignore
  }
  return null;
}

function detectInitialTheme(): Theme {
  const stored = readStoredTheme();
  if (stored) return stored;
  try {
    if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) return "dark";
  } catch {
    // matchMedia unavailable (e.g. tests) — fall through to light
  }
  return "light";
}

// Applies the persisted/system theme to <html> before the first React render
// so dark-mode users do not see a flash of the light theme on initial paint.
export function applyInitialTheme(): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = detectInitialTheme();
}

interface ThemeValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeValue>({
  theme: "light",
  setTheme: () => undefined,
  toggleTheme: () => undefined,
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(detectInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // ignore persistence failures
    }
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggleTheme = useCallback(
    () => setThemeState((current) => (current === "dark" ? "light" : "dark")),
    [],
  );

  const value = useMemo(() => ({ theme, setTheme, toggleTheme }), [theme, setTheme, toggleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

// Falls back to light when a component renders outside the provider (e.g. unit tests).
export function useTheme(): ThemeValue {
  return useContext(ThemeContext);
}
