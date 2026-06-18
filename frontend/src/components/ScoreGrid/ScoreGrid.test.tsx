import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ScoreGrid } from "./ScoreGrid";
import pillStyles from "../Pill/Pill.module.css";

describe("ScoreGrid", () => {
  it("renders a de-camelCased domain label and a score pill per entry", () => {
    render(
      <ScoreGrid
        scores={{
          historyTaking: "Excellent",
          testSelection: "Developing",
        }}
      />,
    );
    expect(screen.getByText("history Taking")).toBeInTheDocument();
    expect(screen.getByText("test Selection")).toBeInTheDocument();

    expect(screen.getByText("Excellent")).toHaveClass(
      pillStyles.scoreExcellent,
    );
    expect(screen.getByText("Developing")).toHaveClass(
      pillStyles.scoreDeveloping,
    );
  });

  it("renders nothing when scores is empty", () => {
    const { container } = render(<ScoreGrid scores={{}} />);
    expect(container.querySelectorAll("span")).toHaveLength(0);
  });
});
