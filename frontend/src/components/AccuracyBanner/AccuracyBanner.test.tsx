import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AccuracyBanner } from "./AccuracyBanner";
import styles from "./AccuracyBanner.module.css";

describe("AccuracyBanner", () => {
  it("renders the correct headline and comment for a correct diagnosis", () => {
    render(<AccuracyBanner accuracy="correct" comment="Spot on." />);
    expect(screen.getByText("✓ Correct diagnosis")).toHaveClass(
      styles.headline,
    );
    expect(screen.getByText("Spot on.")).toHaveClass(styles.comment);
    expect(screen.getByText("✓ Correct diagnosis").parentElement).toHaveClass(
      styles.correct,
    );
  });

  it("maps partially_correct to the amber partial tone", () => {
    render(<AccuracyBanner accuracy="partially_correct" comment="Close." />);
    expect(screen.getByText("◐ Partially correct").parentElement).toHaveClass(
      styles.partial,
    );
  });

  it("maps incorrect to the red incorrect tone", () => {
    render(<AccuracyBanner accuracy="incorrect" comment="Not quite." />);
    expect(screen.getByText("○ Incorrect diagnosis").parentElement).toHaveClass(
      styles.incorrect,
    );
  });
});
