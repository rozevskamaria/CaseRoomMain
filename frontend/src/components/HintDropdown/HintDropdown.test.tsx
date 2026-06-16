import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { HintDropdown } from "./HintDropdown";
import styles from "./HintDropdown.module.css";

describe("HintDropdown", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <HintDropdown open={false} hintsUsed={0} onGetHint={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders the panel with title, description and primary button when open", () => {
    const { container } = render(
      <HintDropdown open hintsUsed={0} onGetHint={() => {}} />,
    );
    expect(container.firstChild).toHaveClass(styles.panel);
    expect(screen.getByText("Ask for guidance")).toHaveClass(styles.title);
    expect(
      screen.getByText(/The hint is personalised/, { exact: false }),
    ).toHaveClass(styles.desc);
    expect(
      screen.getByRole("button", { name: "Get a contextual hint →" }),
    ).toBeInTheDocument();
  });

  it("hides the used-count when hintsUsed is 0", () => {
    const { container } = render(
      <HintDropdown open hintsUsed={0} onGetHint={() => {}} />,
    );
    expect(container.querySelector(`.${styles.usedCount}`)).toBeNull();
  });

  it("shows a singular used-count for one hint", () => {
    render(<HintDropdown open hintsUsed={1} onGetHint={() => {}} />);
    expect(screen.getByText("1 hint used this case")).toBeInTheDocument();
  });

  it("shows a plural used-count for multiple hints", () => {
    render(<HintDropdown open hintsUsed={3} onGetHint={() => {}} />);
    expect(screen.getByText("3 hints used this case")).toBeInTheDocument();
  });

  it("calls onGetHint when the button is clicked", () => {
    const onGetHint = vi.fn();
    render(<HintDropdown open hintsUsed={0} onGetHint={onGetHint} />);
    fireEvent.click(screen.getByRole("button", { name: "Get a contextual hint →" }));
    expect(onGetHint).toHaveBeenCalledTimes(1);
  });
});
