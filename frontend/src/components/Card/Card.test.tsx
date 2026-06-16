import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Card } from "./Card";
import styles from "./Card.module.css";

describe("Card", () => {
  it("renders children with the base card class and default tone", () => {
    render(<Card>Body</Card>);
    const el = screen.getByText("Body");
    expect(el).toHaveClass(styles.card);
    expect(el).toHaveClass(styles.default);
  });

  it("applies tone surface variants", () => {
    const { rerender } = render(<Card tone="teal">x</Card>);
    expect(screen.getByText("x")).toHaveClass(styles.teal);
    rerender(<Card tone="amber">x</Card>);
    expect(screen.getByText("x")).toHaveClass(styles.amber);
    rerender(<Card tone="navy">x</Card>);
    expect(screen.getByText("x")).toHaveClass(styles.navy);
    rerender(<Card tone="red">x</Card>);
    expect(screen.getByText("x")).toHaveClass(styles.red);
  });

  it("applies borderColor and merges style overrides", () => {
    render(
      <Card borderColor="#2A6B5C" style={{ padding: "20px 24px" }}>
        c
      </Card>,
    );
    const el = screen.getByText("c");
    expect(el).toHaveStyle({ borderColor: "#2A6B5C", padding: "20px 24px" });
  });

  it("fires onClick", () => {
    const onClick = vi.fn();
    render(<Card onClick={onClick}>click</Card>);
    fireEvent.click(screen.getByText("click"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
