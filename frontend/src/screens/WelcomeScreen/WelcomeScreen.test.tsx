import { render, screen, fireEvent, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { WelcomeScreen } from "./WelcomeScreen";
import styles from "./WelcomeScreen.module.css";
import { CASE_LIST } from "../../content/caseList";

function baseProps() {
  return {
    mode: "practice" as const,
    seenCases: [] as string[],
    allDone: false,
    showBrowse: false,
    onSetMode: vi.fn(),
    onStartRandom: vi.fn(),
    onStartCase: vi.fn(),
    onToggleBrowse: vi.fn(),
    onResetProgress: vi.fn(),
  };
}

describe("WelcomeScreen", () => {
  it("renders header banner, hero, subtitle and intro", () => {
    render(<WelcomeScreen {...baseProps()} />);
    expect(
      screen.getByText("Rīga Stradiņš University · Faculty of Medicine"),
    ).toBeInTheDocument();
    const hero = screen.getByRole("heading", { level: 1, name: "Clinical Immunology" });
    expect(hero).toHaveClass(styles.heroTitle);
    expect(
      screen.getByText("Immunology Department — Outpatient Clinic Simulator"),
    ).toHaveClass(styles.heroSub);
    expect(
      screen.getByText(/You are a junior doctor working a session/),
    ).toHaveClass(styles.intro);
  });

  it("renders the 6-item numbered how-it-works list", () => {
    const { container } = render(<WelcomeScreen {...baseProps()} />);
    expect(screen.getByText("How the session works")).toBeInTheDocument();
    const numbers = container.querySelectorAll(`.${styles.stepNumber}`);
    expect(numbers).toHaveLength(6);
    expect(Array.from(numbers).map((n) => n.textContent)).toEqual([
      "1",
      "2",
      "3",
      "4",
      "5",
      "6",
    ]);
  });

  it("renders the teal safe-environment callout", () => {
    render(<WelcomeScreen {...baseProps()} />);
    expect(screen.getByText("Safe learning environment.")).toBeInTheDocument();
  });

  it("renders 3 mode cards, marks the active one, and fires onSetMode", () => {
    const props = baseProps();
    const { container } = render(<WelcomeScreen {...props} mode="exam" />);
    const cards = container.querySelectorAll(`.${styles.modeCard}`);
    expect(cards).toHaveLength(3);
    const active = container.querySelectorAll(`.${styles.modeCardActive}`);
    expect(active).toHaveLength(1);
    fireEvent.click(screen.getByText("Reflection mode"));
    expect(props.onSetMode).toHaveBeenCalledWith("reflection");
  });

  it("hides the progress block when nothing is seen", () => {
    const { container } = render(<WelcomeScreen {...baseProps()} />);
    expect(container.querySelector(`.${styles.progress}`)).toBeNull();
  });

  it("renders progress pips and Reset when cases are seen", () => {
    const props = baseProps();
    const { container } = render(
      <WelcomeScreen {...props} seenCases={["xla", "cgd"]} />,
    );
    expect(screen.getByText("2 of 6 cases seen")).toBeInTheDocument();
    const pips = container.querySelectorAll(`.${styles.pip}`);
    expect(pips).toHaveLength(CASE_LIST.length);
    expect(container.querySelectorAll(`.${styles.pipSeen}`)).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(props.onResetProgress).toHaveBeenCalledTimes(1);
  });

  it("shows the remaining count in the CTA and fires onStartRandom", () => {
    const props = baseProps();
    render(<WelcomeScreen {...props} seenCases={["xla"]} />);
    const cta = screen.getByRole("button", {
      name: "See next patient → (5 remaining)",
    });
    fireEvent.click(cta);
    expect(props.onStartRandom).toHaveBeenCalledTimes(1);
  });

  it("shows the bare CTA label when no case is seen yet", () => {
    render(<WelcomeScreen {...baseProps()} />);
    expect(
      screen.getByRole("button", { name: "See next patient →" }),
    ).toBeInTheDocument();
  });

  it("renders the amber all-done callout and disables the CTA when allDone", () => {
    render(<WelcomeScreen {...baseProps()} allDone seenCases={CASE_LIST.map((c) => c.id)} />);
    expect(
      screen.getByText(/You have seen all/),
    ).toBeInTheDocument();
    const cta = screen.getByRole("button", { name: "All cases completed" });
    expect(cta).toBeDisabled();
    expect(cta).toHaveClass(styles.ctaDone);
  });

  it("toggles browse and renders case cards with seen badge + difficulty pill", () => {
    const props = baseProps();
    const { container } = render(
      <WelcomeScreen {...props} showBrowse seenCases={["xla"]} />,
    );
    const cards = container.querySelectorAll(`.${styles.caseCard}`);
    expect(cards).toHaveLength(CASE_LIST.length);

    const xlaCard = screen
      .getByText("A Boy Who Is Always Getting Pneumonia")
      .closest(`.${styles.caseCard}`) as HTMLElement;
    expect(xlaCard).toHaveClass(styles.caseCardSeen);
    expect(within(xlaCard).getByText("✓ seen")).toBeInTheDocument();
    expect(within(xlaCard).getByText("Intermediate")).toBeInTheDocument();
    expect(within(xlaCard).getByText("2-year-old boy · Antibody Deficiency")).toBeInTheDocument();

    fireEvent.click(xlaCard);
    expect(props.onStartCase).toHaveBeenCalledWith("xla");
  });

  it("fires onToggleBrowse from the browse toggle and reflects its label", () => {
    const props = baseProps();
    const { rerender } = render(<WelcomeScreen {...props} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Browse cases individually ↓" }),
    );
    expect(props.onToggleBrowse).toHaveBeenCalledTimes(1);
    rerender(<WelcomeScreen {...props} showBrowse />);
    expect(
      screen.getByRole("button", { name: "Hide case list ↑" }),
    ).toBeInTheDocument();
  });

  it("accepts an explicit cases prop overriding the default list", () => {
    const props = baseProps();
    const cases = [
      {
        id: "solo",
        title: "Solo Case",
        patient: "1-year-old",
        topic: "Test Topic",
        difficulty: "Beginner" as const,
      },
    ];
    render(<WelcomeScreen {...props} cases={cases} showBrowse />);
    expect(screen.getByText("Solo Case")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "See next patient →" }),
    ).toBeInTheDocument();
  });
});
