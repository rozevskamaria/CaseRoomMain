import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { InfoBox } from "./InfoBox";
import styles from "./InfoBox.module.css";

describe("InfoBox", () => {
  it("renders the surface tone with the title above the box", () => {
    const { container } = render(
      <InfoBox
        title="🧭 Ideal reasoning pathway"
        text="Recognise the pattern, then confirm with flow cytometry."
        tone="surface"
      />,
    );
    expect(screen.getByText("🧭 Ideal reasoning pathway")).toHaveClass(
      styles.outerTitle,
    );
    expect(
      screen.getByText(
        "Recognise the pattern, then confirm with flow cytometry.",
      ),
    ).toHaveClass(styles.surfaceBox);
    expect(container.querySelector(`.${styles.navyPaleBox}`)).toBeNull();
  });

  it("renders the navyPale tone with the title inside the box", () => {
    const { container } = render(
      <InfoBox
        title="📖 Suggested revision"
        text="Review B-cell development."
        tone="navyPale"
      />,
    );
    expect(container.querySelector(`.${styles.navyPaleBox}`)).not.toBeNull();
    expect(screen.getByText("📖 Suggested revision")).toHaveClass(
      styles.innerTitle,
    );
    expect(screen.getByText("Review B-cell development.")).toHaveClass(
      styles.innerText,
    );
  });
});
