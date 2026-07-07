import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TextInput } from "./TextInput";

describe("TextInput", () => {
  it("renders a label associated with the input", () => {
    render(
      <TextInput id="x" label="Student ID" value="" onChange={() => {}} />,
    );
    expect(screen.getByLabelText("Student ID")).toBeInTheDocument();
  });

  it("calls onChange with the new value", () => {
    let received = "";
    render(<TextInput value="" onChange={(v) => (received = v)} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "123" } });
    expect(received).toBe("123");
  });

  it("renders a suffix when provided", () => {
    render(<TextInput value="" onChange={() => {}} suffix="@rsu.edu.lv" />);
    expect(screen.getByText("@rsu.edu.lv")).toBeInTheDocument();
  });
});
