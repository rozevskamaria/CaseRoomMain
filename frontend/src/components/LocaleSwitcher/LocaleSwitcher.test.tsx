import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LocaleSwitcher } from "./LocaleSwitcher";

describe("LocaleSwitcher", () => {
  it("renders EN and LV options and marks the active one", () => {
    render(<LocaleSwitcher value="en" onChange={vi.fn()} />);
    const en = screen.getByRole("button", { name: "EN" });
    const lv = screen.getByRole("button", { name: "LV" });
    expect(en).toHaveAttribute("aria-pressed", "true");
    expect(lv).toHaveAttribute("aria-pressed", "false");
  });

  it("fires onChange with the picked locale", () => {
    const onChange = vi.fn();
    render(<LocaleSwitcher value="en" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "LV" }));
    expect(onChange).toHaveBeenCalledWith("lv");
  });

  it("reflects the LV value as active", () => {
    render(<LocaleSwitcher value="lv" onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: "LV" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("disables both options when disabled", () => {
    render(<LocaleSwitcher value="en" onChange={vi.fn()} disabled />);
    expect(screen.getByRole("button", { name: "EN" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "LV" })).toBeDisabled();
  });
});
