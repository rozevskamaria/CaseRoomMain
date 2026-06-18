import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FeedbackList } from "./FeedbackList";
import styles from "./FeedbackList.module.css";

describe("FeedbackList", () => {
  it("renders strip variant items as accent strips", () => {
    render(
      <FeedbackList
        title="✓ What you did well"
        items={["Asked about onset", "Examined tonsils"]}
        variant="strip"
        tone="teal"
      />,
    );
    expect(screen.getByText("✓ What you did well")).toHaveClass(styles.heading);
    const strip = screen.getByText("Asked about onset");
    expect(strip).toHaveClass(styles.strip);
    expect(strip).toHaveClass(styles.accentTeal);
    expect(screen.getByText("Examined tonsils")).toHaveClass(styles.strip);
  });

  it("renders boxedBullets variant inside a box with bullet prefixes", () => {
    const { container } = render(
      <FeedbackList
        title="🔍 Key diagnostic clues in this case"
        items={["Absent B cells"]}
        variant="boxedBullets"
        tone="navy"
      />,
    );
    expect(container.querySelector(`.${styles.box}`)).not.toBeNull();
    const bullet = screen.getByText("• Absent B cells");
    expect(bullet).toHaveClass(styles.boxedBullet);
    expect(bullet).toHaveClass(styles.accentNavy);
  });

  it("renders bareBullets variant with the small heading and accent", () => {
    render(
      <FeedbackList
        title="💊 Management learning points"
        items={["Start IgG replacement"]}
        variant="bareBullets"
        tone="navyLight"
      />,
    );
    expect(screen.getByText("💊 Management learning points")).toHaveClass(
      styles.headingSmall,
    );
    const bullet = screen.getByText("• Start IgG replacement");
    expect(bullet).toHaveClass(styles.bareBullet);
    expect(bullet).toHaveClass(styles.accentNavyLight);
  });
});
