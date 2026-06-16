import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { InfoBanner } from "./InfoBanner";
import styles from "./InfoBanner.module.css";

describe("InfoBanner", () => {
  it("renders the teal tone with message and action slot", () => {
    render(
      <InfoBanner
        tone="teal"
        message="You have enough results to form a differential."
        action={<button>Propose differentials</button>}
      />,
    );
    const msg = screen.getByText(
      "You have enough results to form a differential.",
    );
    expect(msg).toHaveClass(styles.message);
    expect(msg.parentElement).toHaveClass(styles.banner);
    expect(msg.parentElement).toHaveClass(styles.teal);
    expect(
      screen.getByRole("button", { name: "Propose differentials" }),
    ).toBeInTheDocument();
  });

  it("renders the navy tone", () => {
    render(<InfoBanner tone="navy" message="Ready to interpret your results?" />);
    const msg = screen.getByText("Ready to interpret your results?");
    expect(msg.parentElement).toHaveClass(styles.navy);
  });

  it("merges style overrides", () => {
    render(
      <InfoBanner tone="teal" message="m" style={{ padding: "10px 18px" }} />,
    );
    expect(screen.getByText("m").parentElement).toHaveStyle({
      padding: "10px 18px",
    });
  });
});
