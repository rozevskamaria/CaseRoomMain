import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ReflectionDone } from "./ReflectionDone";
import styles from "./ReflectionDone.module.css";

describe("ReflectionDone", () => {
  it("renders the heading, tutor text box and teal callout", () => {
    render(<ReflectionDone tutorText="A thoughtful reflection summary." onReturn={vi.fn()} />);
    const heading = screen.getByRole("heading", { level: 2, name: "Reflection complete" });
    expect(heading).toHaveClass(styles.heading);
    const box = screen.getByText("A thoughtful reflection summary.");
    expect(box).toHaveClass(styles.tutorBox);
    expect(
      screen.getByText(
        "You can return to this case at any time, or explore another case from the library.",
      ),
    ).toBeInTheDocument();
  });

  it("fires onReturn when Return to clinic is clicked", () => {
    const onReturn = vi.fn();
    render(<ReflectionDone tutorText="summary" onReturn={onReturn} />);
    fireEvent.click(screen.getByRole("button", { name: "Return to clinic" }));
    expect(onReturn).toHaveBeenCalledTimes(1);
  });
});
