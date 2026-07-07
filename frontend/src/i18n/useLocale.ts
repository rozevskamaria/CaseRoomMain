import { useCallback, useSyncExternalStore } from "react";
import i18n from "./index";
import type { Locale } from "./types";
import { LOCALES } from "./types";

export const LOCALE_KEY = "iei_locale";

function isLocale(value: string | null): value is Locale {
  return value !== null && (LOCALES as readonly string[]).includes(value);
}

export function readLocale(): Locale {
  try {
    const stored = localStorage.getItem(LOCALE_KEY);
    return isLocale(stored) ? stored : "en";
  } catch {
    return "en";
  }
}

export function writeLocale(locale: Locale): void {
  try {
    localStorage.setItem(LOCALE_KEY, locale);
  } catch {
    return;
  }
}

export function changeLocale(locale: Locale): void {
  writeLocale(locale);
  void i18n.changeLanguage(locale);
}

function subscribe(callback: () => void): () => void {
  i18n.on("languageChanged", callback);
  return () => i18n.off("languageChanged", callback);
}

function getSnapshot(): Locale {
  return isLocale(i18n.language) ? i18n.language : "en";
}

export function useLocale(): { locale: Locale; setLocale: (locale: Locale) => void } {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  const setLocale = useCallback((next: Locale) => changeLocale(next), []);
  return { locale, setLocale };
}
