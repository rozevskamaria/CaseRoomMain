import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Pill } from "./Pill";
import styles from "./Pill.module.css";

describe("Pill", () => {
  it("difficulty tone maps adv/int/beg to the right preset", () => {
    const { rerender } = render(
      <Pill tone="difficulty" value="adv">
        Advanced
      </Pill>,
    );
    expect(screen.getByText("Advanced")).toHaveClass(styles.difficulty);
    expect(screen.getByText("Advanced")).toHaveClass(styles.difficultyAdv);

    rerender(
      <Pill tone="difficulty" value="int">
        Intermediate
      </Pill>,
    );
    expect(screen.getByText("Intermediate")).toHaveClass(styles.difficultyInt);

    rerender(
      <Pill tone="difficulty" value="beg">
        Beginner
      </Pill>,
    );
    expect(screen.getByText("Beginner")).toHaveClass(styles.difficultyBeg);
  });

  it("count tone renders the teal badge", () => {
    render(<Pill tone="count">3</Pill>);
    expect(screen.getByText("3")).toHaveClass(styles.count);
  });

  it("score tone maps each rating to its preset", () => {
    const { rerender } = render(
      <Pill tone="score" value="Excellent">
        Excellent
      </Pill>,
    );
    expect(screen.getByText("Excellent")).toHaveClass(styles.scoreExcellent);

    rerender(
      <Pill tone="score" value="Good">
        Good
      </Pill>,
    );
    expect(screen.getByText("Good")).toHaveClass(styles.scoreGood);

    rerender(
      <Pill tone="score" value="Developing">
        Developing
      </Pill>,
    );
    expect(screen.getByText("Developing")).toHaveClass(styles.scoreDeveloping);

    rerender(
      <Pill tone="score" value="Needs work">
        Needs work
      </Pill>,
    );
    expect(screen.getByText("Needs work")).toHaveClass(styles.scoreOther);
  });

  it("labFlag tone applies geometry class and accepts color via style", () => {
    render(
      <Pill tone="labFlag" style={{ background: "#C03030", color: "#fff" }}>
        CRITICAL
      </Pill>,
    );
    const el = screen.getByText("CRITICAL");
    expect(el).toHaveClass(styles.labFlag);
    expect(el).toHaveStyle({ background: "#C03030", color: "#fff" });
  });
});
