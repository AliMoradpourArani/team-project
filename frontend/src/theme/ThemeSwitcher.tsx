import { useI18n } from "../i18n";
import { useTheme } from "./ThemeProvider";

export default function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();
  const { t } = useI18n();
  const dark = theme === "dark";

  return (
    <button
      className={`theme-switcher${dark ? " dark" : ""}`}
      type="button"
      role="switch"
      aria-checked={dark}
      aria-label={dark ? t("theme.light") : t("theme.dark")}
      title={dark ? t("theme.light") : t("theme.dark")}
      onClick={toggleTheme}
    >
      <span className="theme-track">
        <span className="theme-thumb" aria-hidden="true">
          {dark ? "🌙" : "☀️"}
        </span>
      </span>
    </button>
  );
}
