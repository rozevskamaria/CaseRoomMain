import type { ChangeEventHandler, CSSProperties, KeyboardEvent } from "react";
import { Button } from "../Button";
import styles from "./ChatInput.module.css";

export interface ChatInputProps {
  value: string;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onSend: () => void;
  placeholder?: string;
  disabled?: boolean;
  rows?: number;
  sendLabel?: string;
  style?: CSSProperties;
  className?: string;
}

const sendButtonStyle: CSSProperties = {
  alignSelf: "flex-end",
  padding: "10px 18px",
};

export function ChatInput({
  value,
  onChange,
  onSend,
  placeholder,
  disabled,
  rows = 2,
  sendLabel = "Send",
  style,
  className,
}: ChatInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };
  const rowClasses = [styles.row, className].filter(Boolean).join(" ");
  return (
    <div className={rowClasses} style={style}>
      <textarea
        className={styles.textarea}
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
      />
      <Button
        variant="primary"
        onClick={onSend}
        disabled={disabled || !value.trim()}
        style={sendButtonStyle}
      >
        {sendLabel}
      </Button>
    </div>
  );
}
