import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TypingIndicator } from "./TypingIndicator";
import styles from "./TypingIndicator.module.css";

describe("TypingIndicator", () => {
  it("renders the parent typing bubble with label and body", () => {
    render(<TypingIndicator label="Parent" text="Typing…" />);
    const label = screen.getByText("Parent");
    const body = screen.getByText("Typing…");
    expect(label).toHaveClass(styles.label);
    expect(body).toHaveClass(styles.body);
  });

  it("wraps the bubble in a flex row", () => {
    const { container } = render(
      <TypingIndicator label="Parent" text="Typing…" />,
    );
    const row = container.firstChild as HTMLElement;
    expect(row).toHaveClass(styles.row);
    expect(row.firstChild as HTMLElement).toHaveClass(styles.bubble);
  });

  it("renders the centered variant when no label is given", () => {
    const { container } = render(
      <TypingIndicator text="Generating feedback report…" />,
    );
    const el = container.firstChild as HTMLElement;
    expect(el).toHaveClass(styles.centered);
    expect(el).toHaveTextContent("Generating feedback report…");
  });

  it("merges style overrides", () => {
    const { container } = render(
      <TypingIndicator text="x" style={{ paddingTop: "8px" }} />,
    );
    expect(container.firstChild as HTMLElement).toHaveStyle({
      paddingTop: "8px",
    });
  });
});
