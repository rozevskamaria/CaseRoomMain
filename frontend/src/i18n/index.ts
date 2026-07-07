import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en/common.json";
import lv from "./locales/lv/common.json";
import { LOCALES } from "./types";
import type { Locale } from "./types";

export const LOCALE_STORAGE_KEY = "iei_locale";

function detectInitialLocale(): Locale {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (stored !== null && (LOCALES as readonly string[]).includes(stored)) {
      return stored as Locale;
    }
  } catch {
    return "en";
  }
  return "en";
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { common: en },
    lv: { common: lv },
  },
  lng: detectInitialLocale(),
  fallbackLng: "en",
  defaultNS: "common",
  ns: ["common"],
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
