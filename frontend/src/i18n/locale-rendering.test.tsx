import { afterEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import i18n from "./index";
import { renderWithI18n } from "./test-utils";
import { WelcomeScreen } from "../screens/WelcomeScreen";

function baseProps() {
  return {
    mode: "practice" as const,
    seenCases: [] as string[],
    allDone: false,
    showBrowse: false,
    onSetMode: vi.fn(),
    onSetLanguage: vi.fn(),
    onStartRandom: vi.fn(),
    onStartCase: vi.fn(),
    onToggleBrowse: vi.fn(),
    onResetProgress: vi.fn(),
  };
}

describe("locale rendering", () => {
  afterEach(async () => {
    await i18n.changeLanguage("en");
  });

  it("renders English UI chrome by default", () => {
    renderWithI18n(<WelcomeScreen {...baseProps()} language="en" />, "en");
    expect(screen.getByText("How the session works")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "See next patient →" }),
    ).toBeInTheDocument();
  });

  it("renders Latvian UI chrome when the locale is lv", () => {
    renderWithI18n(<WelcomeScreen {...baseProps()} language="lv" />, "lv");
    expect(screen.getByText("Kā notiek vizīte")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Skatīt nākamo pacientu →" }),
    ).toBeInTheDocument();
  });

  it("keeps clinical-content placeholders out of the catalog (case titles stay as data)", () => {
    renderWithI18n(<WelcomeScreen {...baseProps()} language="lv" showBrowse />, "lv");
    expect(
      screen.getByText("A Boy Who Is Always Getting Pneumonia"),
    ).toBeInTheDocument();
  });
});
