import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { LANGUAGES, translations } from "./translations";
import type { Language, TranslationKey } from "./translations";

const STORAGE_KEY = "team-project.language";

function detectInitialLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "fa" || stored === "de") return stored;
  } catch {
    // localStorage unavailable (e.g. tests) — fall through to default
  }
  return "en";
}

interface I18nValue {
  lang: Language;
  dir: "ltr" | "rtl";
  setLang: (lang: Language) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nValue>({
  lang: "en",
  dir: "ltr",
  setLang: () => undefined,
  t: (key, params) => translate("en", key, params),
});

function translate(
  lang: Language,
  key: TranslationKey,
  params?: Record<string, string | number>,
): string {
  const template = translations[lang][key] ?? translations.en[key] ?? String(key);
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(detectInitialLanguage);
  const dir = useMemo<"ltr" | "rtl">(
    () => LANGUAGES.find((language) => language.code === lang)?.dir ?? "ltr",
    [lang],
  );

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // ignore persistence failures
    }
  }, [lang, dir]);

  const setLang = useCallback((next: Language) => setLangState(next), []);
  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) =>
      translate(lang, key, params),
    [lang],
  );

  const value = useMemo(() => ({ lang, dir, setLang, t }), [lang, dir, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

// Falls back to English when a component renders outside the provider (e.g. unit tests).
export function useI18n(): I18nValue {
  return useContext(I18nContext);
}
