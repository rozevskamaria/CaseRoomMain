export const LOCALES = ["en", "lv"] as const;

export type Locale = (typeof LOCALES)[number];
