import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ChatScreen } from "./ChatScreen";
import {
  caseMeta,
  makeCallbacks,
  makeMessage,
  makeSession,
  makeUi,
} from "../testFixtures";

function renderScreen(opts: {
  sessionOverrides?: Parameters<typeof makeSession>[0];
  uiOverrides?: Parameters<typeof makeUi>[0];
}) {
  const session = makeSession(opts.sessionOverrides);
  const ui = makeUi(opts.uiOverrides);
  const callbacks = makeCallbacks();
  render(
    <ChatScreen
      session={session}
      caseMeta={caseMeta}
      ui={ui}
      callbacks={callbacks}
    />,
  );
  return { callbacks };
}

describe("ChatScreen", () => {
  it("renders the case title and the patient · topic · mode subtitle", () => {
    renderScreen({});
    expect(screen.getByText(caseMeta.title)).toBeInTheDocument();
    expect(
      screen.getByText("2-year-old boy · Antibody Deficiency · Practice Mode"),
    ).toBeInTheDocument();
  });

  it("labels exam mode in the subtitle", () => {
    renderScreen({ uiOverrides: { mode: "exam" } });
    expect(screen.getByText(/Exam Mode/)).toBeInTheDocument();
  });

  it("renders the phase stepper with all phase labels", () => {
    renderScreen({});
    expect(screen.getByText("History Taking")).toBeInTheDocument();
    expect(screen.getByText("Feedback Report")).toBeInTheDocument();
  });

  it("renders the investigations badge equal to the lab message count", () => {
    renderScreen({
      sessionOverrides: {
        messages: [
          makeMessage("lab", "__LAB__CBC\nWBC: 5"),
          makeMessage("lab", "__LAB__CRP\nCRP: 10"),
        ],
      },
    });
    const tab = screen.getByRole("button", { name: /Investigations/ });
    expect(tab).toHaveTextContent("2");
  });

  it("toggles the hint menu open and triggers a hint from the dropdown", () => {
    const { callbacks } = renderScreen({ uiOverrides: { showHintMenu: true } });
    const hintBtn = screen.getByRole("button", { name: /Need a hint/ });
    fireEvent.click(hintBtn);
    expect(callbacks.onShowHintMenu).toHaveBeenCalledWith(false);
    fireEvent.click(screen.getByRole("button", { name: /Get a contextual hint/ }));
    expect(callbacks.onGetHint).toHaveBeenCalled();
  });

  it("opens the hint menu when it is currently closed", () => {
    const { callbacks } = renderScreen({ uiOverrides: { showHintMenu: false } });
    fireEvent.click(screen.getByRole("button", { name: /Need a hint/ }));
    expect(callbacks.onShowHintMenu).toHaveBeenCalledWith(true);
  });

  it("includes the used-count in the hint button label", () => {
    renderScreen({ sessionOverrides: { hintsUsed: 2 } });
    expect(
      screen.getByRole("button", { name: /Need a hint \(2 used\)/ }),
    ).toBeInTheDocument();
  });

  it("hides the hint button in feedback phase", () => {
    renderScreen({ sessionOverrides: { phase: "feedback" } });
    expect(
      screen.queryByRole("button", { name: /Need a hint/ }),
    ).not.toBeInTheDocument();
  });

  it("hides the hint button in reflection phase", () => {
    renderScreen({ sessionOverrides: { phase: "reflection" } });
    expect(
      screen.queryByRole("button", { name: /Need a hint/ }),
    ).not.toBeInTheDocument();
  });

  it("wires the exit button to onExit", () => {
    const { callbacks } = renderScreen({});
    fireEvent.click(screen.getByRole("button", { name: /Exit to clinic/ }));
    expect(callbacks.onExit).toHaveBeenCalled();
  });

  it("switches tabs via the tab bar", () => {
    const { callbacks } = renderScreen({});
    fireEvent.click(screen.getByRole("button", { name: /Final Diagnosis/ }));
    expect(callbacks.onSetTab).toHaveBeenCalledWith("diagnosis");
  });

  it("renders the consultation tab content by default", () => {
    renderScreen({});
    expect(
      screen.getByPlaceholderText("Ask the parent a question…"),
    ).toBeInTheDocument();
  });

  it("renders the investigations tab content when active", () => {
    renderScreen({ uiOverrides: { activeTab: "investigations" } });
    expect(screen.getByText("No investigations ordered yet")).toBeInTheDocument();
  });

  it("renders the diagnosis tab content when active", () => {
    renderScreen({ uiOverrides: { activeTab: "diagnosis" } });
    expect(screen.getByText("Final Diagnosis")).toBeInTheDocument();
  });

  it("renders the hint modal when a hint popup is present", () => {
    const { callbacks } = renderScreen({
      uiOverrides: { hintPopup: "Consider the immune compartment." },
    });
    expect(
      screen.getByText("Consider the immune compartment."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Got it" }));
    expect(callbacks.onCloseHintPopup).toHaveBeenCalled();
  });
});
