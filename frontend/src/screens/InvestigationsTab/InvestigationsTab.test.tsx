import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { InvestigationsTab } from "./InvestigationsTab";
import {
  makeCallbacks,
  makeMessage,
  makeSession,
  makeUi,
} from "../testFixtures";
import type { SessionMessage } from "../types";

function renderTab(opts: {
  sessionOverrides?: Parameters<typeof makeSession>[0];
  uiOverrides?: Parameters<typeof makeUi>[0];
  investMsgs?: SessionMessage[];
  labCount?: number;
}) {
  const session = makeSession(opts.sessionOverrides);
  const ui = makeUi(opts.uiOverrides);
  const callbacks = makeCallbacks();
  const investMsgs =
    opts.investMsgs ??
    session.messages.filter(
      (m) => m.type === "lab" || m.type === "lab_note" || m.type === "lab_tutor",
    );
  const labCount =
    opts.labCount ?? session.messages.filter((m) => m.type === "lab").length;
  render(
    <InvestigationsTab
      session={session}
      ui={ui}
      callbacks={callbacks}
      investMsgs={investMsgs}
      labCount={labCount}
    />,
  );
  return { callbacks };
}

describe("InvestigationsTab", () => {
  it("renders the empty state when there are no investigation messages", () => {
    renderTab({ investMsgs: [] });
    expect(screen.getByText("No investigations ordered yet")).toBeInTheDocument();
  });

  it("renders the ordered-count label and investigation messages", () => {
    renderTab({
      sessionOverrides: { orderedTests: ["CBC", "CRP"] },
      investMsgs: [makeMessage("lab_note", "Note text")],
    });
    expect(screen.getByText("2 investigations ordered")).toBeInTheDocument();
    expect(screen.getByText("Note text")).toBeInTheDocument();
  });

  it("uses singular wording for a single ordered test", () => {
    renderTab({
      sessionOverrides: { orderedTests: ["CBC"] },
      investMsgs: [makeMessage("lab_note", "Note")],
    });
    expect(screen.getByText("1 investigation ordered")).toBeInTheDocument();
  });

  it("renders a lab_tutor message as a tutor card", () => {
    renderTab({ investMsgs: [makeMessage("lab_tutor", "Tutor guidance")] });
    expect(screen.getByText("Tutor guidance")).toBeInTheDocument();
    expect(screen.getByText("🎓 Clinical tutor")).toBeInTheDocument();
  });

  it("shows the propose-differentials banner when labCount >= 3 and phase allows", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "tests" },
      investMsgs: [makeMessage("lab", "__LAB__CBC\nWBC: 5")],
      labCount: 3,
    });
    expect(
      screen.getByText("You have enough results to form a differential."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Propose differentials/ }));
    expect(callbacks.proposeDifferentials).toHaveBeenCalled();
  });

  it("hides the propose-differentials banner in differential phase", () => {
    renderTab({
      sessionOverrides: { phase: "differential" },
      investMsgs: [makeMessage("lab", "__LAB__CBC\nWBC: 5")],
      labCount: 3,
    });
    expect(
      screen.queryByText("You have enough results to form a differential."),
    ).not.toBeInTheDocument();
  });

  it("shows the interpret-results banner when orderedTests >= 2 and phase allows", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "tests", orderedTests: ["CBC", "CRP"] },
      investMsgs: [makeMessage("lab", "__LAB__CBC\nWBC: 5")],
      labCount: 1,
    });
    expect(screen.getByText("Ready to interpret your results?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Interpret results/ }));
    expect(callbacks.interpretResults).toHaveBeenCalled();
  });

  it("renders the interpretation input in interpretation + interp_input", () => {
    const { callbacks } = renderTab({
      sessionOverrides: {
        phase: "interpretation",
        interpText: "my reasoning",
        orderedTests: ["CBC", "CRP"],
      },
      uiOverrides: { inputMode: "interp_input" },
      investMsgs: [makeMessage("lab", "__LAB__CBC\nWBC: 5")],
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit interpretation" }));
    expect(callbacks.onSubmitInterpretation).toHaveBeenCalled();
  });

  it("renders the interp result and next-action buttons when interpResult is set", () => {
    const { callbacks } = renderTab({
      sessionOverrides: {
        phase: "interpretation",
        interpResult: "Great interpretation.",
        orderedTests: ["CBC", "CRP"],
      },
      uiOverrides: { inputMode: "history" },
      investMsgs: [makeMessage("lab", "__LAB__CBC\nWBC: 5")],
    });
    expect(screen.getByText("Great interpretation.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Submit final answer/ }));
    expect(callbacks.submitFinal).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: /Ask the parent more/ }));
    expect(callbacks.onSetTab).toHaveBeenCalledWith("consultation");
    fireEvent.click(screen.getByRole("button", { name: "Order more tests" }));
    expect(callbacks.orderInvestigations).toHaveBeenCalled();
  });

  it("renders the test-order input when not interpreting", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "tests" },
      uiOverrides: { input: "CBC" },
      investMsgs: [makeMessage("lab", "__LAB__CBC\nWBC: 5")],
    });
    const orderBtn = screen.getByRole("button", { name: "Order" });
    fireEvent.click(orderBtn);
    expect(callbacks.onOrderTests).toHaveBeenCalled();
  });
});
