import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EmptyState } from "./EmptyState";
import styles from "./EmptyState.module.css";

describe("EmptyState", () => {
  it("renders icon, title and description", () => {
    render(
      <EmptyState
        icon="🔬"
        title="No investigations ordered yet"
        description="Type test names in the field below."
      />,
    );
    expect(screen.getByText("🔬")).toHaveClass(styles.icon);
    expect(screen.getByText("No investigations ordered yet")).toHaveClass(
      styles.title,
    );
    expect(
      screen.getByText("Type test names in the field below."),
    ).toHaveClass(styles.description);
  });

  it("renders an action slot when provided", () => {
    render(
      <EmptyState
        icon="📋"
        title="Final Diagnosis"
        description="Complete your consultation."
        action={<button>Submit final diagnosis</button>}
      />,
    );
    const btn = screen.getByRole("button", { name: "Submit final diagnosis" });
    expect(btn.parentElement).toHaveClass(styles.action);
  });

  it("does not render the action wrapper when no action", () => {
    const { container } = render(
      <EmptyState icon="🔬" title="t" description="d" />,
    );
    expect(container.querySelector(`.${styles.action}`)).toBeNull();
  });

  it("merges container style overrides (maxWidth / margin via vars)", () => {
    render(
      <EmptyState
        icon="📋"
        title="t"
        description="d"
        style={{ maxWidth: 480 }}
      />,
    );
    expect(screen.getByText("t").parentElement).toHaveStyle({
      maxWidth: "480px",
    });
  });
});
