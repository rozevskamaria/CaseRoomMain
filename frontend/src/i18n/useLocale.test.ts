import { afterEach, beforeEach, describe, expect, it } from "vitest";
import i18n from "./index";
import { LOCALE_KEY, changeLocale, readLocale, writeLocale } from "./useLocale";

describe("useLocale helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(async () => {
    await i18n.changeLanguage("en");
    localStorage.clear();
  });

  it("defaults to en when nothing is stored", () => {
    expect(readLocale()).toBe("en");
  });

  it("reads a stored locale", () => {
    localStorage.setItem(LOCALE_KEY, "lv");
    expect(readLocale()).toBe("lv");
  });

  it("ignores an unknown stored value", () => {
    localStorage.setItem(LOCALE_KEY, "de");
    expect(readLocale()).toBe("en");
  });

  it("writes the locale to localStorage", () => {
    writeLocale("lv");
    expect(localStorage.getItem(LOCALE_KEY)).toBe("lv");
  });

  it("changeLocale persists and switches the i18n language", async () => {
    changeLocale("lv");
    expect(localStorage.getItem(LOCALE_KEY)).toBe("lv");
    await Promise.resolve();
    expect(i18n.language).toBe("lv");
  });
});
