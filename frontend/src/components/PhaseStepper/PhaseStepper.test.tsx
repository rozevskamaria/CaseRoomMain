import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PhaseStepper } from "./PhaseStepper";
import styles from "./PhaseStepper.module.css";

const phases = [
  { key: "history", label: "History Taking" },
  { key: "summary", label: "Clinical Summary" },
  { key: "examination", label: "Physical Examination" },
  { key: "differential", label: "Differential Diagnosis" },
  { key: "tests", label: "Investigations" },
  { key: "interpretation", label: "Interpretation" },
  { key: "final", label: "Final Answer" },
  { key: "feedback", label: "Feedback Report" },
];

describe("PhaseStepper", () => {
  it("renders every phase label in order", () => {
    render(<PhaseStepper phases={phases} currentPhase="history" />);
    phases.forEach((p) => {
      expect(screen.getByText(p.label, { exact: false })).toBeInTheDocument();
    });
  });

  it("marks the current phase active and prior phases done with a ✓ prefix", () => {
    const { container } = render(
      <PhaseStepper phases={phases} currentPhase="examination" />,
    );
    const items = container.querySelectorAll(`.${styles.phaseItem}`);
    expect(items[0]).toHaveClass(styles.done);
    expect(items[1]).toHaveClass(styles.done);
    expect(items[2]).toHaveClass(styles.active);
    expect(items[2]).not.toHaveClass(styles.done);
    expect(items[3]).not.toHaveClass(styles.done);
    expect(items[3]).not.toHaveClass(styles.active);

    expect(items[0]).toHaveTextContent("✓ History Taking");
    expect(items[1]).toHaveTextContent("✓ Clinical Summary");
    expect(items[2]).toHaveTextContent("Physical Examination");
    expect(items[2].textContent).not.toContain("✓");
  });

  it("renders nothing as done when on the first phase", () => {
    const { container } = render(
      <PhaseStepper phases={phases} currentPhase="history" />,
    );
    const items = container.querySelectorAll(`.${styles.phaseItem}`);
    expect(items[0]).toHaveClass(styles.active);
    expect(container.querySelectorAll(`.${styles.done}`)).toHaveLength(0);
  });

  it("applies the container class and style overrides", () => {
    const { container } = render(
      <PhaseStepper phases={phases} currentPhase="history" style={{ opacity: 0.4 }} />,
    );
    const root = container.firstChild as HTMLElement;
    expect(root).toHaveClass(styles.phaseBar);
    expect(root).toHaveStyle({ opacity: "0.4" });
  });
});
