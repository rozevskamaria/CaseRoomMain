import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FeedbackReport } from "./FeedbackReport";
import type { Feedback } from "./FeedbackReport";
import pillStyles from "../Pill/Pill.module.css";

const sampleFeedback: Feedback = {
  diagnosticAccuracy: "correct",
  diagnosticComment: "You correctly identified XLA.",
  wellDone: ["Asked about infection onset", "Noted absent tonsils"],
  missing: ["Did not order flow cytometry early"],
  keyClues: ["Absent B cells on flow cytometry"],
  reasoningPathway: "Pattern-recognise, then confirm with flow cytometry.",
  managementPoints: ["Start IgG replacement"],
  geneticPoints: ["X-linked inheritance"],
  revisionTopic: "Review B-cell development.",
  scores: {
    historyTaking: "Excellent",
    examination: "Good",
    differential: "Good",
    testSelection: "Developing",
    interpretation: "Good",
    management: "Needs review",
  },
};

function renderReport(overrides: Partial<Feedback> = {}, mode = "case") {
  return render(
    <FeedbackReport
      feedback={{ ...sampleFeedback, ...overrides }}
      caseTitle="The Boy With No Tonsils"
      mode={mode}
      onSeeNext={vi.fn()}
      onReflect={vi.fn()}
      onBrowse={vi.fn()}
    />,
  );
}

describe("FeedbackReport", () => {
  it("renders the header, accuracy banner and every section", () => {
    renderReport();
    expect(screen.getByText("Feedback Report")).toBeInTheDocument();
    expect(screen.getByText("The Boy With No Tonsils")).toBeInTheDocument();
    expect(screen.getByText("✓ Correct diagnosis")).toBeInTheDocument();
    expect(
      screen.getByText("You correctly identified XLA."),
    ).toBeInTheDocument();

    expect(screen.getByText("Performance overview")).toBeInTheDocument();
    expect(screen.getByText("✓ What you did well")).toBeInTheDocument();
    expect(screen.getByText("◎ Areas to develop")).toBeInTheDocument();
    expect(
      screen.getByText("🔍 Key diagnostic clues in this case"),
    ).toBeInTheDocument();
    expect(screen.getByText("🧭 Ideal reasoning pathway")).toBeInTheDocument();
    expect(
      screen.getByText("💊 Management learning points"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("🧬 Genetic counselling points"),
    ).toBeInTheDocument();
    expect(screen.getByText("📖 Suggested revision")).toBeInTheDocument();
  });

  it("renders a score pill for each of the six domains", () => {
    const { container } = renderReport();
    const pills = container.querySelectorAll(`.${pillStyles.score}`);
    expect(pills).toHaveLength(6);
    expect(screen.getByText("history Taking")).toBeInTheDocument();
    expect(screen.getByText("Excellent")).toHaveClass(
      pillStyles.scoreExcellent,
    );
    expect(screen.getByText("Needs review")).toHaveClass(pillStyles.scoreOther);
  });

  it("omits the Areas to develop section when missing is empty", () => {
    renderReport({ missing: [] });
    expect(screen.queryByText("◎ Areas to develop")).toBeNull();
  });

  it("hides the reflect action when mode is reflection", () => {
    renderReport({}, "reflection");
    expect(screen.queryByText("Reflect on this case")).toBeNull();
  });
});
