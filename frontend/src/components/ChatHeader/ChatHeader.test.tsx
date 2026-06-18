import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ChatHeader } from "./ChatHeader";
import styles from "./ChatHeader.module.css";

describe("ChatHeader", () => {
  it("renders the title and subtitle", () => {
    render(
      <ChatHeader
        title="A Boy Who Is Always Getting Pneumonia"
        subtitle="2-year-old boy · Antibody Deficiency · Practice Mode"
      />,
    );
    const title = screen.getByText("A Boy Who Is Always Getting Pneumonia");
    expect(title).toHaveClass(styles.title);
    const subtitle = screen.getByText(
      "2-year-old boy · Antibody Deficiency · Practice Mode",
    );
    expect(subtitle).toHaveClass(styles.subtitle);
  });

  it("renders the right slot in the controls wrapper", () => {
    const { container } = render(
      <ChatHeader title="t" subtitle="s" rightSlot={<button>Exit</button>} />,
    );
    const slot = container.querySelector(`.${styles.rightSlot}`);
    expect(slot).not.toBeNull();
    expect(slot).toContainElement(screen.getByRole("button", { name: "Exit" }));
  });

  it("falls back to children when no rightSlot is given", () => {
    const { container } = render(
      <ChatHeader title="t" subtitle="s">
        <button>Hint</button>
      </ChatHeader>,
    );
    const slot = container.querySelector(`.${styles.rightSlot}`);
    expect(slot).toContainElement(screen.getByRole("button", { name: "Hint" }));
  });

  it("applies the container class and style overrides", () => {
    const { container } = render(
      <ChatHeader title="t" subtitle="s" style={{ opacity: 0.3 }} />,
    );
    const root = container.firstChild as HTMLElement;
    expect(root).toHaveClass(styles.chatTop);
    expect(root).toHaveStyle({ opacity: "0.3" });
  });
});
