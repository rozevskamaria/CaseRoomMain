import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./Button";
import styles from "./Button.module.css";

describe("Button", () => {
  it("renders children and defaults to type button + primary variant", () => {
    render(<Button>Send</Button>);
    const btn = screen.getByRole("button", { name: "Send" });
    expect(btn).toHaveAttribute("type", "button");
    expect(btn).toHaveClass(styles.button);
    expect(btn).toHaveClass(styles.primary);
  });

  it("applies the secondary variant class", () => {
    render(<Button variant="secondary">Edit</Button>);
    expect(screen.getByRole("button")).toHaveClass(styles.secondary);
  });

  it("applies the ghost variant class", () => {
    render(<Button variant="ghost">Reset</Button>);
    expect(screen.getByRole("button")).toHaveClass(styles.ghost);
  });

  it("merges style overrides and className (spread-override pattern)", () => {
    render(
      <Button style={{ width: "100%", padding: "10px 18px" }} className="extra">
        Order
      </Button>,
    );
    const btn = screen.getByRole("button");
    expect(btn).toHaveStyle({ width: "100%", padding: "10px 18px" });
    expect(btn).toHaveClass("extra");
  });

  it("fires onClick and respects disabled", () => {
    const onClick = vi.fn();
    const { rerender } = render(<Button onClick={onClick}>Go</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);

    rerender(
      <Button onClick={onClick} disabled>
        Go
      </Button>,
    );
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
