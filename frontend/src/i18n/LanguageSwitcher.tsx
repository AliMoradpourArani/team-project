import { useEffect, useRef, useState } from "react";

import { useI18n } from "./index";
import { LANGUAGES } from "./translations";

export default function LanguageSwitcher() {
  const { lang, setLang, t } = useI18n();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleOutsideClick(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const current = LANGUAGES.find((language) => language.code === lang) ?? LANGUAGES[0];

  return (
    <div className="language-switcher" ref={containerRef}>
      <button
        className="language-trigger"
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t("header.changeLanguage")}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="language-globe" aria-hidden="true">
          🌐
        </span>
        <span className="language-current">{current.nativeLabel}</span>
        <span className={`language-caret${open ? " open" : ""}`} aria-hidden="true">
          ▾
        </span>
      </button>
      <ul
        className={`language-menu${open ? " open" : ""}`}
        role="listbox"
        aria-label={t("header.language")}
      >
        {LANGUAGES.map((language) => (
          <li key={language.code} role="option" aria-selected={language.code === lang}>
            <button
              className={`language-option${language.code === lang ? " active" : ""}`}
              type="button"
              onClick={() => {
                setLang(language.code);
                setOpen(false);
              }}
            >
              <span className="language-native">{language.nativeLabel}</span>
              <span className="language-name">{language.label}</span>
              {language.code === lang ? <span className="language-check">✓</span> : null}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
