import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FeedbackActions } from "./FeedbackActions";

describe("FeedbackActions", () => {
  it("renders all three actions outside reflection mode and wires handlers", () => {
    const onSeeNext = vi.fn();
    const onReflect = vi.fn();
    const onBrowse = vi.fn();
    render(
      <FeedbackActions
        mode="case"
        onSeeNext={onSeeNext}
        onReflect={onReflect}
        onBrowse={onBrowse}
      />,
    );

    fireEvent.click(screen.getByText("See next patient"));
    fireEvent.click(screen.getByText("Reflect on this case"));
    fireEvent.click(screen.getByText("Browse all cases"));

    expect(onSeeNext).toHaveBeenCalledTimes(1);
    expect(onReflect).toHaveBeenCalledTimes(1);
    expect(onBrowse).toHaveBeenCalledTimes(1);
  });

  it("hides the reflect action in reflection mode", () => {
    render(
      <FeedbackActions
        mode="reflection"
        onSeeNext={vi.fn()}
        onReflect={vi.fn()}
        onBrowse={vi.fn()}
      />,
    );
    expect(screen.queryByText("Reflect on this case")).toBeNull();
    expect(screen.getByText("See next patient")).toBeInTheDocument();
    expect(screen.getByText("Browse all cases")).toBeInTheDocument();
  });
});
