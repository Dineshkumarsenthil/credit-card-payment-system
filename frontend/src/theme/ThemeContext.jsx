import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "theme";
const ThemeContext = createContext(null);

// A saved choice wins. Storage can be blocked, so every access is guarded.
function readStored() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

const query = () => window.matchMedia("(prefers-color-scheme: dark)");
const systemTheme = () => (query().matches ? "dark" : "light");

export function ThemeProvider({ children }) {
  const [stored, setStored] = useState(readStored);
  const [system, setSystem] = useState(systemTheme);

  // Until the user picks a theme, follow the computer's setting
  const theme = stored ?? system;

  useEffect(() => {
    const mq = query();
    const onChange = (e) => setSystem(e.matches ? "dark" : "light");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggleTheme = useCallback(() => {
    const next = theme === "dark" ? "light" : "dark";
    setStored(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* the choice still works for this session */
    }
  }, [theme]);

  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used inside <ThemeProvider>");
  return ctx;
}