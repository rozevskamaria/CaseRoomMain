import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { LabeledTextarea } from "./LabeledTextarea";
import styles from "./LabeledTextarea.module.css";

describe("LabeledTextarea", () => {
  it("renders the label and textarea with base input class", () => {
    render(
      <LabeledTextarea
        label="Most likely diagnosis"
        value=""
        onChange={() => {}}
        placeholder="Type here"
      />,
    );
    expect(screen.getByText("Most likely diagnosis")).toHaveClass(styles.label);
    const ta = screen.getByPlaceholderText("Type here");
    expect(ta).toHaveClass(styles.textarea);
    expect(ta.tagName).toBe("TEXTAREA");
  });

  it("reflects value, rows and disabled", () => {
    render(
      <LabeledTextarea
        label="L"
        value="hello"
        onChange={() => {}}
        rows={3}
        disabled
      />,
    );
    const ta = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(ta).toHaveValue("hello");
    expect(ta).toHaveAttribute("rows", "3");
    expect(ta).toBeDisabled();
  });

  it("calls onChange when typing", () => {
    const onChange = vi.fn();
    render(<LabeledTextarea label="L" value="" onChange={onChange} />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "x" },
    });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("merges style overrides on the textarea and labelStyle on the label", () => {
    render(
      <LabeledTextarea
        label="L"
        value=""
        onChange={() => {}}
        style={{ minHeight: 80 }}
        labelStyle={{ color: "#9C978E" }}
      />,
    );
    expect(screen.getByRole("textbox")).toHaveStyle({ minHeight: "80px" });
    expect(screen.getByText("L")).toHaveStyle({ color: "#9C978E" });
  });
});
