import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { HintModal } from "./HintModal";
import styles from "./HintModal.module.css";

describe("HintModal", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <HintModal open={false} text="hi" onClose={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders backdrop, kicker, hint text and Got it button when open", () => {
    const { container } = render(
      <HintModal open text="Consider the immunoglobulins." onClose={() => {}} />,
    );
    expect(container.querySelector(`.${styles.backdrop}`)).not.toBeNull();
    expect(screen.getByText("🎓 Clinical tutor")).toHaveClass(styles.kicker);
    expect(screen.getByText("Consider the immunoglobulins.")).toHaveClass(
      styles.body,
    );
    expect(screen.getByRole("button", { name: "Got it" })).toHaveClass(
      styles.gotIt,
    );
    expect(screen.getByRole("button", { name: "✕" })).toHaveClass(styles.close);
  });

  it("calls onClose when the backdrop is clicked", () => {
    const onClose = vi.fn();
    const { container } = render(
      <HintModal open text="hi" onClose={onClose} />,
    );
    fireEvent.click(container.querySelector(`.${styles.backdrop}`)!);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the ✕ close button is clicked", () => {
    const onClose = vi.fn();
    render(<HintModal open text="hi" onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "✕" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Got it is clicked", () => {
    const onClose = vi.fn();
    render(<HintModal open text="hi" onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Got it" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
