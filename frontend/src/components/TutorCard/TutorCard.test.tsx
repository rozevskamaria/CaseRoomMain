import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TutorCard } from "./TutorCard";
import styles from "./TutorCard.module.css";

describe("TutorCard", () => {
  it("renders the default clinical tutor label and the text", () => {
    render(<TutorCard text="Compare X and Y." />);
    expect(screen.getByText("🎓 Clinical tutor")).toHaveClass(styles.label);
    const body = screen.getByText("Compare X and Y.");
    expect(body).toHaveClass(styles.body);
  });

  it("renders a custom label when provided", () => {
    render(<TutorCard label="Interpretation" text="Looks good." />);
    expect(screen.getByText("Interpretation")).toHaveClass(styles.label);
    expect(screen.queryByText("🎓 Clinical tutor")).toBeNull();
  });

  it("applies the tutor card container class", () => {
    const { container } = render(<TutorCard text="hello" />);
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass(styles.card);
  });

  it("merges style overrides", () => {
    const { container } = render(
      <TutorCard text="hello" style={{ marginBottom: "24px" }} />,
    );
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveStyle({ marginBottom: "24px" });
  });
});
