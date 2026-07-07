import type { ReactElement } from "react";
import { render } from "@testing-library/react";
import type { RenderOptions, RenderResult } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "./index";
import type { Locale } from "./types";

export function renderWithI18n(
  ui: ReactElement,
  locale: Locale = "en",
  options?: Omit<RenderOptions, "wrapper">,
): RenderResult {
  void i18n.changeLanguage(locale);
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>, options);
}
