import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Callout } from "./Callout";
import styles from "./Callout.module.css";

describe("Callout", () => {
  it("renders the teal tone", () => {
    render(<Callout tone="teal">Safe learning environment.</Callout>);
    const el = screen.getByText("Safe learning environment.");
    expect(el).toHaveClass(styles.callout);
    expect(el).toHaveClass(styles.teal);
  });

  it("renders the amber tone", () => {
    render(<Callout tone="amber">You have seen all cases.</Callout>);
    const el = screen.getByText("You have seen all cases.");
    expect(el).toHaveClass(styles.amber);
  });

  it("merges style overrides for per-instance padding/font deltas", () => {
    render(
      <Callout tone="amber" style={{ padding: "14px 18px", fontSize: "13px" }}>
        warn
      </Callout>,
    );
    expect(screen.getByText("warn")).toHaveStyle({
      padding: "14px 18px",
      fontSize: "13px",
    });
  });
});
