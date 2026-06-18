import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ConsultationTab } from "./ConsultationTab";
import {
  caseMeta,
  makeCallbacks,
  makeMessage,
  makeSession,
  makeUi,
  parentMessages,
} from "../testFixtures";
import type { SessionMessage } from "../types";

function renderTab(opts: {
  sessionOverrides?: Parameters<typeof makeSession>[0];
  uiOverrides?: Parameters<typeof makeUi>[0];
  chatMsgs?: SessionMessage[];
}) {
  const session = makeSession(opts.sessionOverrides);
  const ui = makeUi(opts.uiOverrides);
  const callbacks = makeCallbacks();
  const chatMsgs =
    opts.chatMsgs ??
    session.messages.filter(
      (m) => m.type !== "lab" && m.type !== "lab_note" && m.type !== "lab_tutor",
    );
  render(
    <ConsultationTab
      session={session}
      caseMeta={caseMeta}
      ui={ui}
      callbacks={callbacks}
      chatMsgs={chatMsgs}
    />,
  );
  return { callbacks };
}

describe("ConsultationTab", () => {
  it("renders chat messages and the main input by default", () => {
    renderTab({ chatMsgs: [makeMessage("parent", "Hello doctor")] });
    expect(screen.getByText("Hello doctor")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Ask the parent a question…"),
    ).toBeInTheDocument();
  });

  it("shows the parent typing indicator when busy and not feedback", () => {
    renderTab({ uiOverrides: { busy: true } });
    expect(screen.getByText("Typing…")).toBeInTheDocument();
  });

  it("shows the feedback-generating indicator when busy and feedback phase", () => {
    renderTab({ sessionOverrides: { phase: "feedback" }, uiOverrides: { busy: true } });
    expect(screen.getByText("Generating feedback report…")).toBeInTheDocument();
  });

  it("renders the feedback report when phase is feedback and feedback exists", () => {
    renderTab({
      sessionOverrides: {
        phase: "feedback",
        feedback: {
          __typename: "FeedbackType",
          diagnosticAccuracy: "correct",
          diagnosticComment: "Spot on.",
          wellDone: ["a"],
          missing: [],
          keyClues: ["clue"],
          reasoningPathway: "path",
          managementPoints: ["m"],
          geneticPoints: ["g"],
          revisionTopic: "topic",
          scores: {
            __typename: "ScoresType",
            historyTaking: "Good",
            examination: "Good",
            differential: "Good",
            testSelection: "Good",
            interpretation: "Good",
            management: "Good",
          },
        },
      },
    });
    expect(screen.getByText("Feedback Report")).toBeInTheDocument();
    expect(screen.getByText("✓ Correct diagnosis")).toBeInTheDocument();
  });

  it("shows Examine when not done and parentCount >= 2", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { messages: parentMessages(2) },
    });
    const btn = screen.getByRole("button", { name: /Examine patient/ });
    fireEvent.click(btn);
    expect(callbacks.onRequestExam).toHaveBeenCalled();
  });

  it("hides Examine once examDone is true", () => {
    renderTab({ sessionOverrides: { examDone: true, messages: parentMessages(2) } });
    expect(
      screen.queryByRole("button", { name: /Examine patient/ }),
    ).not.toBeInTheDocument();
  });

  it("shows Submit summary only with parentCount >= 3 in history phase", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "history", messages: parentMessages(3) },
    });
    fireEvent.click(screen.getByRole("button", { name: /Submit summary/ }));
    expect(callbacks.goToSummary).toHaveBeenCalled();
  });

  it("hides Submit summary when fewer than 3 parent messages", () => {
    renderTab({ sessionOverrides: { phase: "history", messages: parentMessages(2) } });
    expect(
      screen.queryByRole("button", { name: /Submit summary/ }),
    ).not.toBeInTheDocument();
  });

  it("shows Order investigations with parentCount >= 2", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { messages: parentMessages(2) },
    });
    fireEvent.click(screen.getByRole("button", { name: /Order investigations/ }));
    expect(callbacks.onSetTab).toHaveBeenCalledWith("investigations");
  });

  it("shows Interpret results only with orderedTests >= 2 in tests phase", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "tests", orderedTests: ["CBC", "CRP"] },
    });
    fireEvent.click(screen.getByRole("button", { name: /Interpret results/ }));
    expect(callbacks.interpretResults).toHaveBeenCalled();
  });

  it("hides the action bar entirely in feedback phase", () => {
    renderTab({ sessionOverrides: { phase: "feedback" } });
    expect(screen.queryByText("Next step:")).not.toBeInTheDocument();
  });

  it("renders the summary input in summary_input mode", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "summary", summary: "draft" },
      uiOverrides: { inputMode: "summary_input" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit summary" }));
    expect(callbacks.onSubmitSummary).toHaveBeenCalled();
    expect(
      screen.queryByPlaceholderText("Ask the parent a question…"),
    ).not.toBeInTheDocument();
  });

  it("renders the differential input in diff_input mode", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "differential", differentials: "XLA" },
      uiOverrides: { inputMode: "diff_input" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit differentials" }));
    expect(callbacks.onSubmitDifferentials).toHaveBeenCalled();
  });

  it("renders the reflection input and question in reflection phase", () => {
    const { callbacks } = renderTab({
      sessionOverrides: { phase: "reflection", reflectionStep: 0 },
    });
    expect(screen.getByText(/Reflection question 1 of 5/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "→" }));
    expect(callbacks.onSubmitReflection).toHaveBeenCalled();
    expect(
      screen.queryByPlaceholderText("Ask the parent a question…"),
    ).not.toBeInTheDocument();
  });

  it("hides the main chat input in final phase", () => {
    renderTab({ sessionOverrides: { phase: "final" } });
    expect(
      screen.queryByPlaceholderText("Ask the parent a question…"),
    ).not.toBeInTheDocument();
  });
});
