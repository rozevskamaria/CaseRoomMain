import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ChatInput } from "./ChatInput";
import styles from "./ChatInput.module.css";

describe("ChatInput", () => {
  it("renders a textarea (rows=2 default) and a Send button", () => {
    render(
      <ChatInput
        value="hi"
        onChange={() => {}}
        onSend={() => {}}
        placeholder="Ask the parent a question…"
      />,
    );
    const ta = screen.getByPlaceholderText("Ask the parent a question…");
    expect(ta).toHaveClass(styles.textarea);
    expect(ta).toHaveAttribute("rows", "2");
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });

  it("supports a custom send label (Order)", () => {
    render(
      <ChatInput value="x" onChange={() => {}} onSend={() => {}} sendLabel="Order" />,
    );
    expect(screen.getByRole("button", { name: "Order" })).toBeInTheDocument();
  });

  it("Enter without shift sends; shift+Enter does not", () => {
    const onSend = vi.fn();
    render(<ChatInput value="x" onChange={() => {}} onSend={onSend} />);
    const ta = screen.getByRole("textbox");
    fireEvent.keyDown(ta, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(ta, { key: "Enter", shiftKey: true });
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("clicking Send calls onSend", () => {
    const onSend = vi.fn();
    render(<ChatInput value="x" onChange={() => {}} onSend={onSend} />);
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("disables the send button when value is empty or disabled is set", () => {
    const { rerender } = render(
      <ChatInput value="   " onChange={() => {}} onSend={() => {}} />,
    );
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();

    rerender(
      <ChatInput value="x" onChange={() => {}} onSend={() => {}} disabled />,
    );
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("applies the flex-end send button override", () => {
    render(<ChatInput value="x" onChange={() => {}} onSend={() => {}} />);
    expect(screen.getByRole("button", { name: "Send" })).toHaveStyle({
      alignSelf: "flex-end",
      padding: "10px 18px",
    });
  });
});
