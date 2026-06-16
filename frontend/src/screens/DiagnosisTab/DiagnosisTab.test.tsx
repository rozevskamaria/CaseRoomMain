import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DiagnosisTab } from "./DiagnosisTab";
import { makeCallbacks, makeSession, makeUi } from "../testFixtures";

function renderTab(opts: {
  sessionOverrides?: Parameters<typeof makeSession>[0];
  uiOverrides?: Parameters<typeof makeUi>[0];
}) {
  const session = makeSession(opts.sessionOverrides);
  const ui = makeUi(opts.uiOverrides);
  const callbacks = makeCallbacks();
  render(<DiagnosisTab session={session} ui={ui} callbacks={callbacks} />);
  return { callbacks };
}

describe("DiagnosisTab", () => {
  it("shows the empty state with a gated warning when nothing is ordered or examined", () => {
    renderTab({ sessionOverrides: { orderedTests: [], examDone: false } });
    expect(screen.getByText("Final Diagnosis")).toBeInTheDocument();
    expect(
      screen.getByText(/order at least one investigation before submitting/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Submit final diagnosis/ }),
    ).not.toBeInTheDocument();
  });

  it("enables the submit button when at least one test is ordered", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { orderedTests: ["CBC"] },
    });
    fireEvent.click(screen.getByRole("button", { name: /Submit final diagnosis/ }));
    expect(callbacks.submitFinal).toHaveBeenCalled();
  });

  it("enables the submit button when the exam is done even with no tests", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { orderedTests: [], examDone: true },
    });
    fireEvent.click(screen.getByRole("button", { name: /Submit final diagnosis/ }));
    expect(callbacks.submitFinal).toHaveBeenCalled();
  });

  it("renders all seven final-answer fields when the form is open", () => {
    renderTab({ uiOverrides: { showFinalForm: true } });
    expect(screen.getByText("Submit your final answer")).toBeInTheDocument();
    expect(screen.getByText("Most likely diagnosis")).toBeInTheDocument();
    expect(screen.getByText("Main supporting findings (3–5 bullet points)")).toBeInTheDocument();
    expect(screen.getByText("Differential diagnoses")).toBeInTheDocument();
    expect(screen.getByText("Additional tests or confirmatory testing")).toBeInTheDocument();
    expect(screen.getByText("Initial management plan")).toBeInTheDocument();
    expect(screen.getByText("Genetic counselling and family implications")).toBeInTheDocument();
    expect(screen.getByText("How would you explain this to the parent?")).toBeInTheDocument();
  });

  it("calls onSetFinalAnswerField when a field changes", () => {
    const { callbacks } = renderTab({ uiOverrides: { showFinalForm: true } });
    const textareas = screen.getAllByRole("textbox");
    fireEvent.change(textareas[0], { target: { value: "XLA" } });
    expect(callbacks.onSetFinalAnswerField).toHaveBeenCalledWith("diagnosis", "XLA");
  });

  it("disables submit until the diagnosis field is filled", () => {
    renderTab({ uiOverrides: { showFinalForm: true } });
    expect(screen.getByRole("button", { name: "Submit final answer" })).toBeDisabled();
  });

  it("enables submit once a diagnosis is provided", () => {
    const { callbacks } = renderTab({
      sessionOverrides: {
        finalAnswer: {
          __typename: "FinalAnswerType",
          diagnosis: "XLA",
          findings: "",
          differentials: "",
          tests: "",
          management: "",
          genetics: "",
          explanation: "",
        },
      },
      uiOverrides: { showFinalForm: true },
    });
    const btn = screen.getByRole("button", { name: "Submit final answer" });
    expect(btn).not.toBeDisabled();
    fireEvent.click(btn);
    expect(callbacks.onSubmitFinalAnswer).toHaveBeenCalled();
  });

  it("shows the generating label on the submit button while busy", () => {
    renderTab({
      sessionOverrides: {
        finalAnswer: {
          __typename: "FinalAnswerType",
          diagnosis: "XLA",
          findings: "",
          differentials: "",
          tests: "",
          management: "",
          genetics: "",
          explanation: "",
        },
      },
      uiOverrides: { showFinalForm: true, busy: true },
    });
    expect(screen.getByText("Generating feedback…")).toBeInTheDocument();
  });
});
