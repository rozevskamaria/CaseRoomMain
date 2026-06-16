import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LabFlagBadge } from "./LabFlagBadge";
import styles from "./LabFlagBadge.module.css";

describe("LabFlagBadge", () => {
  it("renders the FLAG_STYLE badge text with badge colours for a flagged key", () => {
    render(<LabFlagBadge flag="crit" />);
    const el = screen.getByText("CRITICAL");
    expect(el).toHaveClass(styles.badge);
    expect(el).toHaveStyle({ background: "#C03030", color: "#fff" });
  });

  it("renders the lo3 arrow badge", () => {
    render(<LabFlagBadge flag="lo3" />);
    const el = screen.getByText("↓↓↓");
    expect(el).toHaveClass(styles.badge);
    expect(el).toHaveStyle({ background: "#2050B0", color: "#fff" });
  });

  it("renders nothing when the flag has a null badge", () => {
    const { container } = render(<LabFlagBadge flag="ok" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing for the neutral flag", () => {
    const { container } = render(<LabFlagBadge flag="neutral" />);
    expect(container).toBeEmptyDOMElement();
  });
});
